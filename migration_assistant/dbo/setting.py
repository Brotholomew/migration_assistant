from sqlalchemy import String, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column
from migration_assistant.repository.instance import database


class Setting(database.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    invenio_address: Mapped[str] = mapped_column(String(80))
    invenio_token: Mapped[str] = mapped_column(String(80))
    cordra_address: Mapped[str] = mapped_column(String(80))
    cordra_token: Mapped[str] = mapped_column(String(80))

    def _set(self, _invenio_address, _invenio_token, _cordra_address, _cordra_token):
        self.invenio_address = _invenio_address
        self.invenio_token = _invenio_token
        self.cordra_address = _cordra_address
        self.cordra_token = _cordra_token

    def __init__(self, *, invenio_address, invenio_token, cordra_address, cordra_token):
        self._set(invenio_address, invenio_token, cordra_address, cordra_token)

    def update(self, _setting):
        self._set(_setting.invenio_address, _setting.invenio_token, _setting.cordra_address, _setting.cordra_token)

    def to_string(self):
        return f"settings object:\n - invenio_address: {self.invenio_address}\n - invenio_token: {self.invenio_token}\n - cordra_address: {self.cordra_address}\n - cordra_token: {self.cordra_token}"