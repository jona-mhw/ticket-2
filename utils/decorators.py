"""
Decorators - Reusable function decorators for routes
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Decorator to require admin privileges for a route.
    Redirects to dashboard if user is not admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


def superuser_required(f):
    """
    Decorator to require superuser privileges for a route.
    Redirects to admin index if user is not superuser.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'is_superuser') or not current_user.is_superuser:
            flash('Acceso denegado. Se requieren permisos de Superusuario.', 'error')
            return redirect(url_for('admin.index'))
        return f(*args, **kwargs)
    return decorated_function
