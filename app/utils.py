import json
import jwt
import functools
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


# JWT Settings
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def error_response(message, status_code=400, errors=None):
    """Standard error response format"""
    response = {
        'success': False,
        'message': message,
    }
    if errors:
        response['errors'] = errors
    return JsonResponse(response, status=status_code)


def success_response(data=None, message='Success', status_code=200):
    """Standard success response format"""
    response = {
        'success': True,
        'message': message,
    }
    if data is not None:
        response['data'] = data
    return JsonResponse(response, status=status_code)


def handle_exceptions(view_func):
    """Decorator for global exception handling"""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except json.JSONDecodeError:
            return error_response('Invalid JSON in request body', 400)
        except jwt.ExpiredSignatureError:
            return error_response('Token has expired', 401)
        except jwt.InvalidTokenError:
            return error_response('Invalid token', 401)
        except Exception as e:
            if settings.DEBUG:
                return error_response(str(e), 500)
            return error_response('Internal server error', 500)
    return wrapper


def auth_required(view_func):
    """Decorator to require JWT authentication"""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return error_response('Authorization header missing or invalid', 401)
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.user_id = payload.get('user_id')
            request.user_data = payload
        except jwt.ExpiredSignatureError:
            return error_response('Token has expired', 401)
        except jwt.InvalidTokenError:
            return error_response('Invalid token', 401)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def generate_jwt_token(user):
    """Generate JWT token for a user"""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def require_methods(methods):
    """Decorator to restrict HTTP methods"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method not in methods:
                return error_response(
                    f'Method {request.method} not allowed',
                    405
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
