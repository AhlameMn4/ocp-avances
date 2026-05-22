from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_rh:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def gestionnaire_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_gestionnaire:
            raise PermissionDenied
        if not request.user.actif:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper