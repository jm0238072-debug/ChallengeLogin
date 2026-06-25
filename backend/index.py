from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from config.database import (
    get_db_connection, get_user_by_email, create_user,
    update_login_attempts, set_session_id, clear_session_id,
    get_user_by_id, update_activity
)
import bcrypt
from datetime import datetime, timedelta
import secrets
import os
from dotenv import load_dotenv

load_dotenv()  # Cargar variables desde .env

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../assets')
app.secret_key = os.getenv('SECRET_KEY', 'clave-super-secreta-cambiar-en-produccion')

# ---------- Decorador login_required ----------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión primero.', 'error')
            return redirect(url_for('index'))
        
        if 'last_activity' in session:
            if (datetime.now() - session['last_activity']).total_seconds() > 900:
                session.clear()
                flash('Tu sesión ha expirado por inactividad.', 'error')
                return redirect(url_for('index'))
        session['last_activity'] = datetime.now()
        
        user = get_user_by_id(session['user_id'])
        if not user or user['session_id'] != session.get('session_id'):
            session.clear()
            flash('Se detectó otra sesión activa con tu cuenta.', 'error')
            return redirect(url_for('index'))
        
        update_activity(session['user_id'])
        return f(*args, **kwargs)
    return decorated_function

# ---------- Ruta principal ----------
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    
    if request.method == 'POST':
        if request.form.get('csrf_token') != session.get('csrf_token'):
            abort(403)
        
        if 'registro' in request.form:
            nombre = request.form.get('nombre', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            ok, msg = create_user(nombre, email, password)
            if ok:
                flash(msg, 'success')
                session['csrf_token'] = secrets.token_hex(16)
            else:
                flash(msg, 'error')
        
        elif 'login' in request.form:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            user = get_user_by_email(email)
            if not user:
                flash('El correo ingresado no está registrado.', 'error')
                return redirect(url_for('index'))
            
            if user['bloqueado_hasta'] and user['bloqueado_hasta'] > datetime.now():
                delta = user['bloqueado_hasta'] - datetime.now()
                horas = delta.seconds // 3600
                minutos = (delta.seconds % 3600) // 60
                flash(f'Cuenta bloqueada por seguridad. Intente nuevamente en {horas}h {minutos}m.', 'error')
                return redirect(url_for('index'))
            
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                update_login_attempts(user['id'], success=True)
                session['user_id'] = user['id']
                session['user_nombre'] = user['nombre']
                session['last_activity'] = datetime.now()
                session_id = secrets.token_hex(16)
                session['session_id'] = session_id
                set_session_id(user['id'], session_id)
                flash(f'¡Bienvenido {user["nombre"]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                update_login_attempts(user['id'], success=False)
                user_updated = get_user_by_email(email)
                if user_updated['intentos_fallidos'] >= 3:
                    flash('Has excedido el límite de 3 intentos. Cuenta bloqueada por 2 horas.', 'error')
                else:
                    restantes = 3 - user_updated['intentos_fallidos']
                    flash(f'Credenciales incorrectas. Te quedan {restantes} intentos.', 'error')
                return redirect(url_for('index'))
    
    return render_template('index.html', csrf_token=session.get('csrf_token'))

# ---------- Dashboard ----------
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_user_by_id(session['user_id'])
    return render_template('dashboard.html', nombre=user['nombre'])

# ---------- Logout ----------
@app.route('/logout')
def logout():
    if 'user_id' in session:
        clear_session_id(session['user_id'])
    session.clear()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)