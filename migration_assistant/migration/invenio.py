import json

from migration_assistant.dbo.setting import Setting
import requests as rq


class Invenio:
    def __init__(self, _settings: Setting):
        self.url = _settings.invenio_address
        self.token = _settings.invenio_token

    def get_auth_header(self) -> str:
        return 'Bearer ' + self.token

    def get_default_headers(self, content_type: str = 'application/json') -> dict:
        return {
            'Authorization': self.get_auth_header(),
            "Content-Type": content_type,
        }

    def get_all_records(self):
        pass

    def get_record_metadata(self, record):
        pass

    def get_record_fdo(self, record):
        pass