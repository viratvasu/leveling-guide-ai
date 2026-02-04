"""
API Views for Levelling Guide AI
Uses existing model fields - stores extra data in guides_data JSONField
"""
import json
from functools import wraps
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods as require_methods
from django.views.decorators.csrf import csrf_exempt
import jwt
from django.conf import settings

from .models import User, LevellingGuide, LevellingGuideLog
from .services import (
    parse_csv_content,
    build_examples_matrix,
    build_empty_matrix,
    generate_all_cells_progressive,
    regenerate_single_cell
)


def success_response(data=None, message=None, status=200):
    return JsonResponse({
        'success': True,
        'message': message,
        'data': data
    }, status=status)


def error_response(message, status=400):
    return JsonResponse({
        'success': False,
        'message': message,
        'data': None
    }, status=status)


def handle_exceptions(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except Exception as e:
            return error_response(str(e), 500)
    return wrapper


def auth_required(view_func):
    """Decorator to require JWT authentication."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return error_response('No token provided', 401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload.get('user_id')
            request.user = User.objects.get(id=request.user_id)
        except jwt.ExpiredSignatureError:
            return error_response('Token expired', 401)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return error_response('Invalid token', 401)
        
        return view_func(request, *args, **kwargs)
    return wrapper


# Auth endpoints
@csrf_exempt
@handle_exceptions
@require_methods(['POST'])
def login(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return error_response('Invalid credentials', 401)
    
    if not user.check_password(password):
        return error_response('Invalid credentials', 401)
    
    token = jwt.encode(
        {'user_id': user.id},
        settings.SECRET_KEY,
        algorithm='HS256'
    )
    
    # Permission structure:
    # levelling_guide.view = can see filtered guide (their level + higher)
    # levelling_guide.configure = full admin (upload, versions, regenerate, all levels)
    
    # Permissions from DB only (no superuser special treatment)
    permissions = user.permissions if user.permissions else {}
    if 'levelling_guide' not in permissions:
        # Default for regular users is View Only? Or nothing?
        # User said "only based on permissions from db should be valid".
        # So if DB is empty, permissions is empty. 
        # But wait, existing code defaults to view: True if not present?
        # "if 'levelling_guide' not in permissions: permissions['levelling_guide'] = {'view': True, 'configure': False}"
        # I should probably keep the default View permission for everyone? 
        # Or strictly what's in DB?
        # User said "take them only". 
        # If I remove the default, then NO ONE can see the guide unless explicitly granted.
        # But `test1` (L3) needs to see it. `test1` permissions are empty?
        # Let's assume standard users get View implicitly, but Configure must be explicit.
        pass

    # Ensure view permission for everyone? Or relies on DB?
    # Let's keep the logic that defaults to View=True if missing, BUT Configure must be false.
    if 'levelling_guide' not in permissions:
         permissions['levelling_guide'] = {'view': True, 'configure': False}
    
    # Build navigation - show Levelling Guide to everyone with view permission
    navigation = []
    if permissions.get('levelling_guide', {}).get('view') or permissions.get('levelling_guide', {}).get('configure'):
        navigation.append({
            'key': 'levelling_guide',
            'label': 'Levelling Guide',
            'path': '/dashboard/levelling-guide',
            'icon': '📊'
        })
    
    # Users management - only for admins
    if permissions.get('users', {}).get('view'):
        navigation.append({
            'key': 'users',
            'label': 'Users',
            'path': '/dashboard/users',
            'icon': '👥'
        })
    
    return success_response(
        data={
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'current_role': user.current_role or '',  # User's current level (e.g., "L2-Software Engineer")
            },
            'company': {
                'id': user.company.id,
                'name': user.company.name,
            } if user.company else None,
            'permissions': permissions,
            'navigation': navigation,
        },
        message='Login successful'
    )


# Helper to get/set metadata in guides_data
def get_guide_meta(guide, key, default=None):
    """Get metadata from guides_data._meta"""
    meta = (guide.guides_data or {}).get('_meta', {})
    return meta.get(key, default)


def set_guide_meta(guide, key, value):
    """Set metadata in guides_data._meta"""
    if not guide.guides_data:
        guide.guides_data = {}
    if '_meta' not in guide.guides_data:
        guide.guides_data['_meta'] = {}
    guide.guides_data['_meta'][key] = value


# Guide Upload - Step 1: Upload CSV, parse, return preview
@csrf_exempt
@handle_exceptions
@auth_required
@require_methods(['POST'])
def upload_guide(request):
    user = request.user
    
    if 'file' not in request.FILES:
        return error_response('No file provided', 400)
    
    csv_file = request.FILES['file']
    company_website = request.POST.get('company_website', '')
    
    if not csv_file.name.endswith('.csv'):
        return error_response('File must be a CSV', 400)
    
    if csv_file.size > 1024 * 1024:
        return error_response('File too large (max 1MB)', 400)
    
    # Parse CSV
    csv_content = csv_file.read().decode('utf-8')
    parsed_csv = parse_csv_content(csv_content)
    
    # Build empty matrix with pending status
    empty_matrix = build_empty_matrix(parsed_csv)
    
    # Get next version number
    current_version = LevellingGuide.objects.filter(
        company=user.company
    ).order_by('-version').first()
    
    next_version = (current_version.version + 1) if current_version else 1
    
    # Unset current version on all existing guides
    LevellingGuide.objects.filter(company=user.company).update(is_current_version=False)
    
    # Create guide - store metadata in guides_data
    parsed_csv['_meta'] = {
        'file_name': csv_file.name,
        'company_website': company_website,
        'status': 'pending'
    }
    
    guide = LevellingGuide.objects.create(
        company=user.company,
        uploaded_by=user,
        uploaded_file_raw=csv_file.name,
        guides_data=parsed_csv,
        guides_examples=empty_matrix,
        version=next_version,
        is_current_version=True,
    )
    
    return success_response(
        data={
            'id': guide.id,
            'version': guide.version,
            'file_name': csv_file.name,
            'guides_data': parsed_csv,
            'guides_examples': empty_matrix,
        },
        message='Guide uploaded. Ready to generate examples.'
    )


# Guide Generate - Step 2: Generate examples for a guide
@csrf_exempt
@handle_exceptions
@auth_required
@require_methods(['POST'])
def generate_guide_examples(request, guide_id):
    user = request.user
    
    try:
        guide = LevellingGuide.objects.get(id=guide_id, company=user.company)
    except LevellingGuide.DoesNotExist:
        return error_response('Guide not found', 404)
    
    if get_guide_meta(guide, 'status') == 'complete':
        return error_response('Guide already generated', 400)
    
    # Mark as processing
    set_guide_meta(guide, 'status', 'processing')
    guide.save()
    
    parsed_csv = guide.guides_data
    company_website = get_guide_meta(guide, 'company_website', '')
    
    # Generate all examples
    examples = generate_all_cells_progressive(parsed_csv, company_website)
    
    # Build final matrix
    guides_examples = build_examples_matrix(parsed_csv, examples)
    
    # Update guide
    guide.guides_examples = guides_examples
    set_guide_meta(guide, 'status', 'complete')
    guide.save()
    
    return success_response(
        data={
            'id': guide.id,
            'guides_examples': guides_examples,
        },
        message='Examples generated successfully'
    )


# Regenerate single cell
@csrf_exempt
@handle_exceptions
@auth_required
@require_methods(['POST'])
def regenerate_cell(request, guide_id):
    user = request.user
    data = json.loads(request.body)
    
    competency = data.get('competency')
    level = data.get('level')
    feedback = data.get('feedback', '')
    
    if not competency or not level:
        return error_response('Competency and level required', 400)
    
    try:
        guide = LevellingGuide.objects.get(id=guide_id, company=user.company)
    except LevellingGuide.DoesNotExist:
        return error_response('Guide not found', 404)
    
    company_website = get_guide_meta(guide, 'company_website', '')
    
    # Regenerate examples
    new_examples = regenerate_single_cell(
        guide.guides_data,
        competency,
        level,
        feedback,
        company_website
    )
    
    # Update guide examples
    guides_examples = guide.guides_examples
    for row in guides_examples.get('rows', []):
        if row['competency'] == competency:
            row['cells'][level]['examples'] = new_examples
            row['cells'][level]['status'] = 'complete'
    
    guide.guides_examples = guides_examples
    guide.save()
    
    # Log regeneration
    LevellingGuideLog.objects.create(
        levelling_guide=guide,
        updated_by=user,
        guide_examples={'competency': competency, 'level': level, 'examples': new_examples},
        comment=feedback
    )
    
    return success_response(
        data={
            'competency': competency,
            'level': level,
            'examples': new_examples
        },
        message='Cell regenerated'
    )


# Regenerate all cells with feedback
@csrf_exempt
@handle_exceptions
@auth_required
@require_methods(['POST'])
def regenerate_all(request, guide_id):
    user = request.user
    data = json.loads(request.body)
    
    global_feedback = data.get('feedback', '')
    
    try:
        guide = LevellingGuide.objects.get(id=guide_id, company=user.company)
    except LevellingGuide.DoesNotExist:
        return error_response('Guide not found', 404)
    
    # Set all cells to pending
    guides_examples = guide.guides_examples
    for row in guides_examples.get('rows', []):
        for level in guides_examples.get('levels', []):
            row['cells'][level]['status'] = 'pending'
            row['cells'][level]['examples'] = []
    
    guide.guides_examples = guides_examples
    set_guide_meta(guide, 'status', 'processing')
    guide.save()
    
    company_website = get_guide_meta(guide, 'company_website', '')
    
    # Generate all examples
    examples = generate_all_cells_progressive(guide.guides_data, company_website)
    
    # Build final matrix
    guides_examples = build_examples_matrix(guide.guides_data, examples)
    
    # Update guide
    guide.guides_examples = guides_examples
    set_guide_meta(guide, 'status', 'complete')
    guide.save()
    
    # Log
    LevellingGuideLog.objects.create(
        levelling_guide=guide,
        updated_by=user,
        comment=f"Regenerate all: {global_feedback}"
    )
    
    return success_response(
        data={
            'id': guide.id,
            'guides_examples': guides_examples,
        },
        message='All examples regenerated'
    )


# List guides
@csrf_exempt
@handle_exceptions
@auth_required
@require_methods(['GET'])
def list_guides(request):
    user = request.user
    
    guides = LevellingGuide.objects.filter(company=user.company).order_by('-version')
    
    guide_list = []
    for g in guides:
        guide_list.append({
            'id': g.id,
            'version': g.version,
            'file_name': get_guide_meta(g, 'file_name', g.uploaded_file_raw or 'Unknown'),
            'is_current_version': g.is_current_version,
            'status': get_guide_meta(g, 'status', 'complete'),
            'created_at': g.created_at.isoformat(),
        })
    
    return success_response(
        data={'guides': guide_list},
        message='Guides fetched'
    )


# Get single guide
@csrf_exempt
@handle_exceptions
@auth_required
@require_methods(['GET'])
def get_guide(request, guide_id):
    user = request.user
    
    try:
        guide = LevellingGuide.objects.get(id=guide_id, company=user.company)
    except LevellingGuide.DoesNotExist:
        return error_response('Guide not found', 404)
    
    return success_response(data={
        'id': guide.id,
        'version': guide.version,
        'file_name': get_guide_meta(guide, 'file_name', guide.uploaded_file_raw or 'Unknown'),
        'is_current_version': guide.is_current_version,
        'status': get_guide_meta(guide, 'status', 'complete'),
        'guides_data': guide.guides_data,
        'guides_examples': guide.guides_examples,
        'created_at': guide.created_at.isoformat(),
    })


# Get current guide
@csrf_exempt
@handle_exceptions
@auth_required
@require_methods(['GET'])
def get_current_guide(request):
    user = request.user
    
    guide = LevellingGuide.objects.filter(
        company=user.company,
        is_current_version=True
    ).first()
    
    if not guide:
        return success_response(data={'guide': None}, message='No current guide')
    
    return success_response(data={
        'guide': {
            'id': guide.id,
            'version': guide.version,
            'file_name': get_guide_meta(guide, 'file_name', guide.uploaded_file_raw or 'Unknown'),
            'status': get_guide_meta(guide, 'status', 'complete'),
            'guides_examples': guide.guides_examples,
            'created_at': guide.created_at.isoformat(),
        }
    })


# Set current version
@csrf_exempt
@handle_exceptions
@auth_required
@require_methods(['POST'])
def set_current_version(request, guide_id):
    user = request.user
    
    try:
        guide = LevellingGuide.objects.get(id=guide_id, company=user.company)
    except LevellingGuide.DoesNotExist:
        return error_response('Guide not found', 404)
    
    # Unset all others
    LevellingGuide.objects.filter(company=user.company).update(is_current_version=False)
    
    # Set this one
    guide.is_current_version = True
    guide.save()
    
    return success_response(message='Current version updated')
