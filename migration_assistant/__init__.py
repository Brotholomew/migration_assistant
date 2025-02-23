import os
from flask import Flask
from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

import migration_assistant.repository.init as repository_init
from  migration_assistant.front.home import home

configuration_variables = {
    'FLASK_LOG_LEVEL': 'WARNING',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///app.db'
}

class Base(DeclarativeBase):
  pass

def create_app():
    app = Flask(__name__, instance_relative_config=True, template_folder='front/templates', static_folder='front/static')
    app.config.from_pyfile('config.py', silent=True)

    for variable, default_value in configuration_variables.items():
        if variable not in app.config.keys():
            if variable not in os.environ.keys():
                app.logger.warning(f"{variable} not configured, using the default: {default_value}")
                app.config[variable] = default_value
            else:
                app.config[variable] = os.environ[variable]

    app.logger.setLevel(app.config['FLASK_LOG_LEVEL'])

    repository_init.init(app)
    app.register_blueprint(home.bp)

    CORS(app)

    # TODO: delete
    # with app.app_context():
    #      repository_setting.get_setting()
    #
    # @app.route('/')
    # def hw():
    #    return f"<p>log level = {app.config['FLASK_LOG_LEVEL']}, sql url = {app.config['SQLALCHEMY_DATABASE_URI']}</p>"

    return app