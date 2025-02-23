from sqlalchemy import select

from migration_assistant.dbo.mapping import Mapping
from migration_assistant.repository.init import database

def get_mapping(invenio_key: str) -> Mapping | None:
    mappings = database.session.execute(select(Mapping).where(Mapping.invenio_key == invenio_key)).all()
    return mappings[0] if mappings is not None and len(mappings) > 0 else None

def add_mapping(invenio_key: str, cordra_key: str) -> Mapping:
    mapping = Mapping(
        invenio_key=invenio_key,
        cordra_key=cordra_key
    )

    database.session.add(mapping)
    database.session.commit()

    return mapping