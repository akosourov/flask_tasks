import sqlite3
from flask import current_app, g
from werkzeug.security import generate_password_hash


DB_CONNECTION_TIMEOUT = 2    # seconds

ADMIN_ROLE = 'ADMIN'
VIEWER_ROLE = 'VIEWER'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'],
                               timeout=DB_CONNECTION_TIMEOUT)
        # todo row_factory
        g.db.row_factory = sqlite3.Row    # marshall to dict
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource('scheme.sql') as fd:
        db.executescript(fd.read().decode('utf8'))
        print("DB structure was created")

    insert_role(ADMIN_ROLE)
    insert_role(VIEWER_ROLE)
    insert_user(current_app.config['ADMIN_NAME'],
                generate_password_hash(current_app.config['ADMIN_PASSWORD']),
                role=ADMIN_ROLE)
    print("Initial data was created")


def init_app(app):
    # close db connection on request complete
    app.teardown_appcontext(close_db)


def get_user(username=None, user_id=None):
    db = get_db()
    if username is not None:
        cursor = db.execute("""
            SELECT users.id, username, hashed_password, roles.role
            FROM users
                JOIN roles ON roles.id = users.role_id
            WHERE username = ?""", (username,))
    elif user_id is not None:
        cursor = db.execute("""
            SELECT users.id, username, hashed_password, roles.role 
            FROM users 
               JOIN roles ON roles.id = users.role_id
            WHERE users.id = ?""", (user_id,))
    else:
        return None
    return cursor.fetchone()


def insert_user(username, hashed_password, role=None):
    db = get_db()
    if role is None:
        role = VIEWER_ROLE
    db.execute("""
        WITH R AS (
            SELECT id FROM roles WHERE role = ?
        )
        INSERT INTO users (username, hashed_password, role_id) 
        VALUES (?, ?, (SELECT R.id FROM R))""", (role, username, hashed_password))
    db.commit()
    return get_user(username)


# todo must be in transaction
def update_user(user_id, username=None, hashed_password=None, role_name=None):
    db = get_db()
    placeholders = []
    params = []
    if username is not None:
        placeholders.append('username = ?')
        params.append(username)
    if hashed_password is not None:
        placeholders.append('hashed_password = ?')
        params.append(hashed_password)
    if role_name is not None:
        role = get_role(role_name)
        if role is None:
            role = insert_role(role_name)
            placeholders.append('role_id = ?')
            params.append(role['id'])
    params.append(user_id)
    if placeholders:
        db.execute("""
            UPDATE users
            SET {}
            WHERE id = ?
        """.format(', '.join(placeholders)), params)
        db.commit()


class DBError(Exception):
    pass


def get_users_list():
    db = get_db()
    cursor = db.execute("""
        SELECT users.id, users.username, users.hashed_password, roles.role
        FROM users
            JOIN roles ON roles.id = users.role_id""")
    return cursor.fetchall()


def is_admin(user_id):
    db = get_db()
    cursor = db.execute("""
        SELECT roles.role AS role
        FROM users 
           JOIN roles ON roles.id = users.role_id
        WHERE users.id = ?""", (user_id,))
    user_role = cursor.fetchone()
    return user_role is not None and user_role['role'] == 'ADMIN'


def insert_role(role):
    db = get_db()
    db.execute('INSERT INTO roles (role) VALUES (?)', (role,))
    db.commit()
    return get_role(role)


def get_role(role_name):
    db = get_db()
    cursor = db.execute('SELECT id, role FROM roles WHERE role = ?', (role_name,))
    return cursor.fetchone()
