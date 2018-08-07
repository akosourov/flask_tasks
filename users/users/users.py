from flask import (Blueprint, render_template, request, flash,
                   redirect, url_for, g, abort)
from werkzeug.security import generate_password_hash

from users import db
from users.auth import login_required, admin_required


bp = Blueprint('users', __name__)


@bp.route('/')
@login_required
def index():
    users_list = db.get_users_list()
    return render_template('users/index.html', users_list=users_list)


@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_name = request.form['role']
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif not role_name:
            error = 'Role is required'

        if error is not None:
            flash(error)
        else:
            try:
                db.insert_role(role_name)
                db.insert_user(username, password, role=role_name)
            except db.DBError:
                # already exists
                pass

            return redirect(url_for('index'))

    return render_template('users/user.html')


@bp.route('/update/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def update(user_id):
    user = db.get_user(user_id=user_id)
    if user is None:
        return abort(404)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_name = request.form['role']
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif not role_name:
            error = 'Role is required'

        if error:
            flash(error)

        try:
            db.insert_role(role_name)
        except db.DBError:
            # role already exists
            pass

        db.update_user(user_id, username=username,
                       hashed_password=generate_password_hash(password),
                       role_name=role_name)
        return redirect(url_for('index'))

    return render_template('users/user.html',
                           username=user['username'],
                           password=user['hashed_password'],
                           role=user['role'])
