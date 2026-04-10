"""
RBAC decorators for MedTrack.

Usage:
    from pdl.decorators import role_required

    @role_required('admin', 'staff')
    def my_view(request): ...

Roles defined in pdl.models.UserRole:
    admin, staff, doctor, pharmacist

Django superusers always bypass role checks.
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def role_required(*roles):
    """
    Restrict a view to users whose UserProfile.role is one of *roles.
    Superusers bypass all checks. Unauthenticated users are redirected to login.
    Authenticated users without the required role receive HTTP 403.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            # Superusers always have full access
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            try:
                role = request.user.userprofile.role
            except Exception:
                raise PermissionDenied

            if role not in roles:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator