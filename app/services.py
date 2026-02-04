"""
Anthropic AI Service for generating leveling guide examples.
Improved prompts, consistent across generation and regeneration, increased parallelism.
"""

import json
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings


# Configuration
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 600  # Per cell - 3 examples with some buffer
TEMPERATURE = 0.7
MAX_WORKERS = 20  # Increased for faster parallel processing


def build_system_prompt(parsed_csv: dict, company_website: str = None) -> str:
    """
    Build comprehensive system prompt with FULL CSV context.
    Same prompt used for both initial generation and regeneration.
    """
    
    levels = parsed_csv.get("levels", [])
    competencies = parsed_csv.get("competencies", {})
    
    # Build complete leveling framework as structured data
    framework_text = "=" * 60 + "\n"
    framework_text += "COMPLETE LEVELING FRAMEWORK\n"
    framework_text += "=" * 60 + "\n\n"
    
    # Show level progression
    framework_text += f"LEVELS (from junior to senior): {' → '.join(levels)}\n\n"
    
    # Show all competencies with all level descriptions
    framework_text += "COMPETENCIES AND EXPECTATIONS BY LEVEL:\n"
    framework_text += "-" * 40 + "\n\n"
    
    for comp_name, level_descs in competencies.items():
        framework_text += f"📌 {comp_name}\n"
        for level in levels:
            desc = level_descs.get(level, "Not defined")
            framework_text += f"   [{level}]: {desc}\n"
        framework_text += "\n"
    
    # Company context
    company_text = ""
    if company_website:
        company_text = f"""
COMPANY CONTEXT:
Website: {company_website}
Tailor examples to be relevant for this company's domain and culture.
"""
    
    system_prompt = f"""You are an expert HR consultant specializing in career development and leveling frameworks. Your role is to generate specific, observable, and actionable examples that demonstrate expected behaviors at each career level.

{company_text}
{framework_text}

YOUR TASK:
Generate exactly 3 real-world examples that show what someone at the specified level would DO on a day-to-day basis for the given competency.

RULES FOR EXAMPLES:
1. Each example must be 1-2 sentences max
2. Use action verbs (e.g., "Writes", "Leads", "Mentors", "Designs")
3. Be SPECIFIC - mention actual tools, processes, or situations
4. Show OBSERVABLE behavior (things a manager can see/verify)
5. Match the seniority level - junior vs senior expectations are DIFFERENT
6. Avoid vague language like "helps with", "assists", "supports" for senior levels

OUTPUT FORMAT:
Return ONLY valid JSON in this exact format:
{{"examples": ["Example 1 text", "Example 2 text", "Example 3 text"]}}

Do not include any explanation, markdown, or text outside the JSON."""

    return system_prompt


def build_user_prompt(competency: str, level: str, description: str, user_feedback: str = None, previous_examples: list = None) -> str:
    """
    Build user prompt for cell generation.
    Same structure for both initial generation and regeneration.
    """
    
    user_prompt = f"""Generate 3 observable behavioral examples for:

COMPETENCY: {competency}
LEVEL: {level}
EXPECTATION: {description}
"""
    
    # For regeneration - show what was generated before
    if previous_examples and len(previous_examples) > 0:
        user_prompt += f"""
PREVIOUS EXAMPLES (to improve upon):
{chr(10).join(f'- {ex}' for ex in previous_examples)}
"""
    
    # User feedback for regeneration
    if user_feedback:
        user_prompt += f"""
USER FEEDBACK (incorporate this):
{user_feedback}
"""
    
    user_prompt += """
Return JSON: {"examples": ["...", "...", "..."]}"""
    
    return user_prompt


def generate_cell_examples(
    client: anthropic.Anthropic,
    system_prompt: str,
    competency: str,
    level: str,
    description: str,
    user_feedback: str = None,
    previous_examples: list = None
) -> list:
    """
    Generate examples for a single cell.
    Works for both initial generation and regeneration.
    """
    
    user_prompt = build_user_prompt(
        competency=competency,
        level=level,
        description=description,
        user_feedback=user_feedback,
        previous_examples=previous_examples
    )
    
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        text = response.content[0].text.strip()
        
        # Clean markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (```json and ```)
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        
        # Handle potential JSON wrapped in backticks
        text = text.strip("`").strip()
        
        data = json.loads(text)
        examples = data.get("examples", [])
        
        # Validate we got a list of strings
        if isinstance(examples, list) and all(isinstance(e, str) for e in examples):
            return examples[:3]  # Ensure max 3
        
        return []
        
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return data.get("examples", [])[:3]
            except:
                pass
        return []
    except Exception as e:
        print(f"Error generating examples for {competency}/{level}: {e}")
        return []


def generate_all_cells(
    parsed_csv: dict,
    company_website: str = None,
    on_cell_complete: callable = None
) -> dict:
    """
    Generate examples for all cells in parallel.
    
    Args:
        parsed_csv: Parsed CSV structure
        company_website: Optional company context URL
        on_cell_complete: Optional callback(competency, level, examples)
    
    Returns:
        {competency: {level: [examples], ...}, ...}
    """
    
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    system_prompt = build_system_prompt(parsed_csv, company_website)
    
    levels = parsed_csv.get("levels", [])
    competencies = parsed_csv.get("competencies", {})
    
    results = {}
    
    # Create all cell tasks
    tasks = []
    for comp_name, level_descs in competencies.items():
        results[comp_name] = {}
        for level in levels:
            desc = level_descs.get(level, "")
            tasks.append((comp_name, level, desc))
    
    # Process in parallel with increased workers
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for comp_name, level, desc in tasks:
            future = executor.submit(
                generate_cell_examples,
                client,
                system_prompt,
                comp_name,
                level,
                desc,
                None,  # No user feedback for initial generation
                None   # No previous examples for initial generation
            )
            futures[future] = (comp_name, level)
        
        for future in as_completed(futures):
            comp_name, level = futures[future]
            try:
                examples = future.result(timeout=60)  # Increased timeout
                results[comp_name][level] = examples
                
                if on_cell_complete:
                    on_cell_complete(comp_name, level, examples)
                    
            except Exception as e:
                print(f"Timeout/Error for {comp_name}/{level}: {e}")
                results[comp_name][level] = []
    
    return results


def regenerate_single_cell(
    parsed_csv: dict,
    competency: str,
    level: str,
    user_feedback: str,
    company_website: str = None,
    previous_examples: list = None
) -> list:
    """
    Regenerate examples for a single cell with user feedback.
    Uses the SAME system prompt as initial generation for consistency.
    """
    
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    # SAME system prompt as initial generation
    system_prompt = build_system_prompt(parsed_csv, company_website)
    
    description = parsed_csv.get("competencies", {}).get(competency, {}).get(level, "")
    
    return generate_cell_examples(
        client=client,
        system_prompt=system_prompt,
        competency=competency,
        level=level,
        description=description,
        user_feedback=user_feedback,
        previous_examples=previous_examples
    )


# Keep old function name for backwards compatibility
def generate_all_cells_progressive(
    parsed_csv: dict,
    company_website: str = None,
    on_cell_complete: callable = None
) -> dict:
    """Alias for generate_all_cells for backwards compatibility."""
    return generate_all_cells(parsed_csv, company_website, on_cell_complete)


def parse_csv_content(csv_content: str) -> dict:
    """Parse CSV content into structured format."""
    import csv
    from io import StringIO
    
    reader = csv.reader(StringIO(csv_content))
    rows = list(reader)
    
    if len(rows) < 2:
        raise ValueError("CSV must have at least header row and one data row")
    
    header = rows[0]
    levels = header[1:]  # Skip first column (competency name)
    
    competencies = {}
    for row in rows[1:]:
        if len(row) < 2:
            continue
        
        competency_name = row[0].strip()
        if not competency_name:  # Skip empty rows
            continue
            
        level_descriptions = {}
        
        for i, level in enumerate(levels):
            if i + 1 < len(row):
                # Clean up multiline text and extra whitespace
                desc = row[i + 1].strip()
                desc = ' '.join(desc.split())  # Normalize whitespace
                level_descriptions[level.strip()] = desc
        
        competencies[competency_name] = level_descriptions
    
    return {
        "levels": [l.strip() for l in levels if l.strip()],
        "competencies": competencies
    }


def build_examples_matrix(parsed_csv: dict, examples: dict) -> dict:
    """Build final matrix structure for UI display."""
    levels = parsed_csv.get("levels", [])
    competencies = parsed_csv.get("competencies", {})
    
    rows = []
    for competency, level_descs in competencies.items():
        cells = {}
        comp_examples = examples.get(competency, {})
        
        for level in levels:
            cell_examples = comp_examples.get(level, [])
            cells[level] = {
                "description": level_descs.get(level, ""),
                "examples": cell_examples,
                "status": "complete" if cell_examples else "pending"
            }
        
        rows.append({
            "competency": competency,
            "cells": cells
        })
    
    return {
        "levels": levels,
        "rows": rows
    }


def build_empty_matrix(parsed_csv: dict) -> dict:
    """Build empty matrix structure with pending status for all cells."""
    levels = parsed_csv.get("levels", [])
    competencies = parsed_csv.get("competencies", {})
    
    rows = []
    for competency, level_descs in competencies.items():
        cells = {}
        for level in levels:
            cells[level] = {
                "description": level_descs.get(level, ""),
                "examples": [],
                "status": "pending"
            }
        
        rows.append({
            "competency": competency,
            "cells": cells
        })
    
    return {
        "levels": levels,
        "rows": rows
    }
