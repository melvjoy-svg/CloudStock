from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def staff_permission_required(flag):
    """Owners/super admins have full access; staff must have the requested flag."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role in ('SUPER_ADMIN', 'BUSINESS_OWNER') or getattr(request.user, flag, False):
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Your staff account does not have this permission.')
            return redirect('dashboard')
        return wrapper
    return decorator
