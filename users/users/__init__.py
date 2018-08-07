from flask import Flask


default_config = dict(
    SECRET_KEY='dev',
    DATABASE='dev.sqlite',
    ADMIN_NAME='admin',
    ADMIN_PASSWORD= 'admin'
)


def create_app(config_file_name=None):
    app = Flask(__name__, instance_relative_config=True)
    if config_file_name is None:
        app.config.from_mapping(**default_config)
    else:
        app.config.from_pyfile(config_file_name)

    from . import db
    with app.app_context():
        db.init_db()

    db.init_app(app)

    from . import auth, users
    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.add_url_rule('/', endpoint='index')   # makes index == blog.index

    return app
