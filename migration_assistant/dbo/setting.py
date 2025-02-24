from sqlalchemy import String, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column
from migration_assistant.repository.instance import database


class Setting(database.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    invenio_address: Mapped[str] = mapped_column(String(80))
    invenio_token: Mapped[str] = mapped_column(String(80))
    cordra_address: Mapped[str] = mapped_column(String(80))
    cordra_username: Mapped[str] = mapped_column(String(80))
    cordra_password: Mapped[str] = mapped_column(String(80))

    def _set(self, _invenio_address, _invenio_token, _cordra_address, _cordra_username, _cordra_password):
        self.invenio_address = _invenio_address
        self.invenio_token = _invenio_token
        self.cordra_address = _cordra_address
        self.cordra_username = _cordra_username
        self.cordra_password = _cordra_password

    def __init__(self, *, invenio_address, invenio_token, cordra_address, _cordra_username, _cordra_password):
        self._set(invenio_address, invenio_token, cordra_address, _cordra_username, _cordra_password)

    def update(self, _setting):
        self._set(_setting.invenio_address, _setting.invenio_token, _setting.cordra_address, _setting.cordra_username, _setting.cordra_password)