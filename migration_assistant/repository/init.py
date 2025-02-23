from migration_assistant.dbo.setting import Setting
from migration_assistant.dbo.mapping import Mapping
from migration_assistant.repository.instance import database
from flask import Flask

def init(app: Flask) -> None:
    database.init_app(app)
    with app.app_context():
        database.create_all()

    app.config['repository'] = database