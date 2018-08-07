import functools

from flask import (Blueprint, request, redirect, url_for, render_template,
                   flash, session, g, abort)
from werkzeug.security import generate_password_hash, check_password_hash
from users import db


bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        error = validate_form_required(request.form)
        if error is None:
            username = request.form['username']
            password = request.form['password']

            user = db.get_user(username)
            if user is None:
                try:
                    user = db.insert_user(username, generate_password_hash(password))
                except db.DBError:
                    error = 'User {} already exists'.format(username)
                else:
                    if user:
                        set_session(user['id'])
                        return redirect(url_for('index'))
                    # concurrent transaction might delete user
                    return redirect(url_for('auth.register'))
            else:
                error = 'User {} already exists'.format(username)

        flash(error)   # share to render_template

    return render_template('auth/register.html')


@bp.route('login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        error = validate_form_required(request.form)
        if error is None:
            username = request.form['username']
            password = request.form['password']
            user = db.get_user(username)
            if user is None:
                error = 'Incorrect username'
            elif not check_password_hash(user['hashed_password'], password):
                error = 'Incorrect password'
            else:
                set_session(user['id'])
                return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.get_user(user_id=user_id)


def login_required(view):
    @functools.wraps(view)
    def _view(*args, **kwargs):
        if g.user is None:
            return redirect('auth/login')
        return view(*args, **kwargs)
    return _view


def admin_required(view):
    @functools.wraps(view)
    def _view(*args, **kwargs):
        if g.user is None:
            return abort(403)
        if not db.is_admin(g.user['id']):
            return abort(403)
        return view(*args, **kwargs)
    return _view


def validate_form_required(form):
    if not form['username']:
        return 'Username is required'
    if not form['password']:
        return 'Password is required'
    return None


def set_session(user_id):
    session.clear()
    session['user_id'] = user_id
