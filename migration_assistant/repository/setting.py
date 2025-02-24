from sqlalchemy import select

from migration_assistant.dbo.setting import Setting
from migration_assistant.repository.instance import database

def get_setting() -> Setting | None:
    settings = database.session.execute(select(Setting)).scalars().first()
    return settings if settings is not None else None

def set_settings(*, invenio_address: str, invenio_token: str, cordra_address: str, cordra_username: str, cordra_password: str) -> Setting:
    current_setting = get_setting()
    new_setting = Setting(
        invenio_address=invenio_address,
        invenio_token=invenio_token,
        cordra_address=cordra_address,
        _cordra_username=cordra_username,
        _cordra_password=cordra_password
    )

    if current_setting is None:
        database.session.add(new_setting)
        database.session.commit()
    else:
        current_setting.update(new_setting)
        database.session.commit()

    return new_setting if current_setting is None else current_setting