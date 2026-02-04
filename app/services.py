"""
Anthropic AI Service for generating leveling guide examples.
Uses prompt caching for cost efficiency - full CSV as system prompt, one cell per request.
"""

import json
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings


# Configuration
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 500  # Per cell - only 3 examples needed
TEMPERATURE = 0.7


def get_system_prompt_with_csv(parsed_csv: dict, company_website: str = None) -> str:
    """Build system prompt with full CSV context for caching."""
    
    levels = parsed_csv.get("levels", [])
    competencies = parsed_csv.get("competencies", {})
    
    # Build CSV context
    csv_context = "LEVELING FRAMEWORK:\n"
    csv_context += f"Levels: {', '.join(levels)}\n\n"
    
    for comp_name, level_descs in competencies.items():
        csv_context += f"Competency: {comp_name}\n"
        for level, desc in level_descs.items():
            csv_context += f"  {level}: {desc}\n"
        csv_context += "\n"
    
    company_context = ""
    if company_website:
        company_context = f"\nCompany Context: {company_website}\n"
    
    return f"""You are an expert HR consultant generating specific, actionable examples for a leveling framework.
{company_context}
{csv_context}
Rules:
- Generate exactly 3 examples
- Keep examples SHORT (1-2 sentences each)
- Focus on OBSERVABLE actions (what someone actually does day-to-day)
- Examples should be CONCRETE and ACTIONABLE
- Show behavior appropriate for the specific level

Return JSON only: {{"examples": ["example 1", "example 2", "example 3"]}}"""


def generate_cell_examples(
    client: anthropic.Anthropic,
    system_prompt: str,
    competency: str,
    level: str,
    description: str,
    user_feedback: str = None
) -> list:
    """Generate examples for a single cell."""
    
    user_prompt = f"Generate 3 observable examples for:\nCompetency: {competency}\nLevel: {level}\nDescription: {description}"
    
    if user_feedback:
        user_prompt += f"\n\nUser feedback for improvement: {user_feedback}"
    
    user_prompt += "\n\nReturn JSON: {\"examples\": [\"...\", \"...\", \"...\"]}"
    
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        text = response.content[0].text.strip()
        
        # Clean markdown if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        
        data = json.loads(text)
        return data.get("examples", [])
        
    except Exception:
        return []


def generate_all_cells_progressive(
    parsed_csv: dict,
    company_website: str = None,
    on_cell_complete: callable = None
) -> dict:
    """
    Generate examples for all cells with progress callback.
    
    Args:
        parsed_csv: Parsed CSV structure
        company_website: Optional company context
        on_cell_complete: Callback(competency, level, examples) called when each cell completes
    
    Returns:
        {competency: {level: [examples], ...}, ...}
    """
    
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    system_prompt = get_system_prompt_with_csv(parsed_csv, company_website)
    
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
    
    # Process in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for comp_name, level, desc in tasks:
            future = executor.submit(
                generate_cell_examples,
                client,
                system_prompt,
                comp_name,
                level,
                desc
            )
            futures[future] = (comp_name, level)
        
        for future in as_completed(futures):
            comp_name, level = futures[future]
            try:
                examples = future.result(timeout=30)
                results[comp_name][level] = examples
                
                if on_cell_complete:
                    on_cell_complete(comp_name, level, examples)
                    
            except Exception:
                results[comp_name][level] = []
    
    return results


def regenerate_single_cell(
    parsed_csv: dict,
    competency: str,
    level: str,
    user_feedback: str,
    company_website: str = None
) -> list:
    """Regenerate examples for a single cell with user feedback."""
    
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    system_prompt = get_system_prompt_with_csv(parsed_csv, company_website)
    
    description = parsed_csv.get("competencies", {}).get(competency, {}).get(level, "")
    
    return generate_cell_examples(
        client,
        system_prompt,
        competency,
        level,
        description,
        user_feedback
    )


def parse_csv_content(csv_content: str) -> dict:
    """Parse CSV content into structured format."""
    import csv
    from io import StringIO
    
    reader = csv.reader(StringIO(csv_content))
    rows = list(reader)
    
    if len(rows) < 2:
        raise ValueError("CSV must have at least header row and one data row")
    
    header = rows[0]
    levels = header[1:]
    
    competencies = {}
    for row in rows[1:]:
        if len(row) < 2:
            continue
        
        competency_name = row[0].strip()
        level_descriptions = {}
        
        for i, level in enumerate(levels):
            if i + 1 < len(row):
                # Clean up multiline text
                desc = row[i + 1].strip().replace('\n', ' ').replace('  ', ' ')
                level_descriptions[level.strip()] = desc
        
        competencies[competency_name] = level_descriptions
    
    return {
        "levels": [l.strip() for l in levels],
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
            cells[level] = {
                "description": level_descs.get(level, ""),
                "examples": comp_examples.get(level, []),
                "status": "complete" if comp_examples.get(level) else "pending"
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
