import json

from migration_assistant.dbo.setting import Setting
import base64
import requests as rq

class Cordra:
    def __init__(self, _setting: Setting):
        self.url = _setting.cordra_address
        self.user = _setting.cordra_username
        self.password = _setting.cordra_password
        self.prefix = None

    def get_auth_header(self) -> str:
        auth_str = f"{self.user}:{self.password}"
        auth_str_bytes = auth_str.encode("utf-8")
        b64_bytes = base64.b64encode(auth_str_bytes)
        return f'Basic {b64_bytes.decode("utf-8")}'

    def get_default_headers(self, content_type: str = 'application/json') -> dict:
        return {
                "Content-Type": content_type,
                "Authorization": self.get_auth_header()
        }

    def get_design(self) -> dict:
        response = rq.post(
            url=f"{self.url}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
            headers=self.get_default_headers(),
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'Failed to fetch design at: {self.url}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service')

        return response.json()

    def get_prefix(self) -> str:
        design = self.get_design()
        self.prefix = design['handleMintingConfig']['prefix']
        return self.prefix

    def schema_present(self, schema: str) -> dict | None:
        design = self.get_design()
        if schema not in design['schemas']:
            return None

        return design['schemas'][schema]

    def post_schema(self, name: str, schema: str):
        schema = self.resolve_prefix(schema)
        schema_json = json.loads(schema)
        response = rq.put(
            url=f"{self.url}/schemas/{name}",
            json=schema_json,
            headers=self.get_default_headers(),
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'Failed to post schema at: {self.url}/schemas/{name}')

    def object_present(self, name) -> dict | None:
        response = rq.get(
            url=f"{self.url}/cordra/doip/0.DOIP/Op.Retrieve?targetId={self.get_prefix()}/{name}",
            headers=self.get_default_headers(),
            verify=False
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None

    def create_object(self, name: str, json_string: str):
        json_string = self.resolve_prefix(json_string)
        _obj = self.object_present(name)
        if _obj is not None:
            return _obj

        response = rq.post(
            url=f"{self.url}/objects/?type=FDO-configuration&suffix={name}",
            headers=self.get_default_headers(),
            data=json_string,
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'failed to create {name}:{response.text}')

        return response.json()

    def update_object(self, name: str, json_string: str):
        json_string = self.resolve_prefix(json_string)
        _obj = self.object_present(name)
        if _obj is None:
            return self.create_object(name, json_string)

        response = rq.put(
            url=f"{self.url}/objects/{self.get_prefix()}/{name}",
            headers=self.get_default_headers(),
            data=json_string,
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'failed to update {name}:{response.text}')

        return response.json()

    def resolve_prefix(self, _str: str) -> str:
        return _str.replace("CORDRA_PREFIX", self.get_prefix())

    def update_schema_with_js(self, name: str, js: str):
        # refresh cordra schemas
        response = rq.get(
            url=f"{self.url}/schemas/{name}",
            headers=self.get_default_headers(),
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'schema {name} not found')

        design = self.get_design()

        schema_id = None
        for _id, schema in design['schemaIds'].items():
            if schema == name:
                schema_id = _id

        if schema_id is None:
            raise Exception(f'schema {name} not found')

        response = rq.get(
            url=f"{self.url}/objects/{schema_id}?full=true",
            headers=self.get_default_headers(),
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'failed to update schema: {name}')

        schema_json = response.json()
        schema_json['content']['javascript'] = js

        # delete the schema
        response = rq.delete(
            url=f"{self.url}/schemas/{name}",
            headers=self.get_default_headers(),
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'failed to delete schema: {name}: {response.text}')

        print(schema_json)

        response = rq.post(
            url=f"{self.url}/uploadObjects",
            headers=self.get_default_headers(),
            verify=False,
            json={
                "results": [schema_json]
            }
        )

        if response.status_code != 200:
            raise Exception(f'failed to update schema: {name}: {response.text}')

        return response.json()