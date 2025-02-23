from sqlalchemy import String, Column
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column

from migration_assistant.repository.instance import database

class Mapping(database.Model):
    invenio_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    cordra_key: Mapped[str] = mapped_column(String(80), primary_key=True)