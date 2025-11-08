from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, LoginAudit, ROLE_VISUALIZADOR
from datetime import datetime
from auth_iap import hybrid_auth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """
    Punto de entrada principal para la autenticación.
    Prioriza IAP y redirige a login de demo si no es una solicitud IAP (y demo login está habilitado).
    """
    # Si es una solicitud de IAP, intentar autenticar.
    if hybrid_auth.is_iap_request():
        success, message_or_user = hybrid_auth.authenticate_request()
        if success:
            # IAP OK y usuario encontrado en la BD y activo
            if current_user.role == ROLE_VISUALIZADOR:
                return redirect(url_for('visualizador.dashboard'))
            return redirect(url_for('tickets.nursing_board'))
        else:
            # IAP OK pero usuario no en BD, o IAP falló
            email = hybrid_auth.get_current_user_email()
            return render_template('unauthorized.html', email=email, message=message_or_user)

    # Si no es una solicitud IAP (entorno local)
    # Verificar si el login demo está habilitado
    if hybrid_auth.enable_demo_login:
        # Redirigir al login de demo
        return redirect(url_for('auth.demo_login'))
    else:
        # Login demo deshabilitado, solo se permite acceso por IAP
        current_app.logger.warning("Intento de acceso a /login sin IAP y con ENABLE_DEMO_LOGIN=false")
        return render_template('unauthorized.html',
                             email=None,
                             message="Solo se permite acceso a través de Google IAP. El login tradicional está deshabilitado."), 403

@auth_bp.route('/demo/login', methods=['GET', 'POST'])
def demo_login():
    """
    Página de login para demostración y desarrollo local.
    Solo disponible si ENABLE_DEMO_LOGIN=true.
    """
    # Verificar si el login demo está habilitado
    if not hybrid_auth.enable_demo_login:
        current_app.logger.warning("Intento de acceso a /demo/login con ENABLE_DEMO_LOGIN=false")
        return render_template('unauthorized.html',
                             email=None,
                             message="El login tradicional está deshabilitado. Solo se permite acceso a través de Google IAP."), 403

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Por favor complete todos los campos.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user)
            session['auth_type'] = 'traditional'  # Marcar como login tradicional

            # Audit log
            try:
                audit_log = LoginAudit(
                    user_id=user.id,
                    username=user.username,
                    clinic_id=user.clinic_id,
                    ip_address=request.remote_addr
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                flash(f'Error al registrar auditoría: {str(e)}', 'warning')
                db.session.rollback()

            flash(f'¡Bienvenido, {user.username}!', 'success')
            if user.role == ROLE_VISUALIZADOR:
                return redirect(url_for('visualizador.dashboard'))
            return redirect(url_for('tickets.nursing_board'))
        else:
            flash('Credenciales inválidas o usuario inactivo.', 'error')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Detectar si el usuario entró por IAP o login tradicional
    auth_type = session.get('auth_type', 'traditional')

    # Cerrar sesión de Flask
    logout_user()

    # Limpiar la sesión
    session.clear()

    # Redirigir según el tipo de autenticación
    if auth_type == 'iap':
        # Usuario IAP: cerrar sesión de Google completamente
        # Esto fuerza al usuario a volver a autenticarse con Google
        return redirect('https://accounts.google.com/Logout')
    else:
        # Usuario tradicional: redirigir a login normalmente
        flash('Sesión cerrada exitosamente.', 'success')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout-success')
def logout_success():
    """Página de confirmación de logout para usuarios IAP"""
    is_iap_logout = request.args.get('is_iap', 'false') == 'true'
    return render_template('logout_success.html', is_iap_logout=is_iap_logout)

@auth_bp.route('/iap-status')
def iap_status():
    """Endpoint para verificar estado de IAP"""
    return {
        'iap_enabled': hybrid_auth.enable_iap,
        'is_iap_request': hybrid_auth.iap_auth.is_iap_request(),
        'user_email': hybrid_auth.get_current_user_email(),
        'current_user': current_user.username if current_user.is_authenticated else None
    }
