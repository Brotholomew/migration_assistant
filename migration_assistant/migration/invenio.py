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

    def mimetype_accepted(self, mimetype):
        # make a broken request
        response = rq.get(
            url=f"{self.url}/api/records/non-existent",
            headers={
                "Authorization": self.get_auth_header(),
                "Accept": 'non-existent',
            },
            verify=False
        )

        # it is intended to get a 406 response
        if response.status_code == 200:
            return False

        if 'message' not in response.json():
            return False

        types = response.json()['message'].replace("Invalid 'Accept' header. Expected one of: ", "").split(", ")
        print(types)
        return mimetype in types

    def proxy_content_negotiation(self, record_id: str, mimetype: str | None):
        _headers = {
            "Authorization": self.get_auth_header()
        }

        if mimetype is not None:
            _headers['Accept'] = mimetype

        return rq.get(
            url=f"{self.url}/api/records/{record_id}",
            headers=_headers,
            verify=False
        )

    def get_response(self, req):
        response = rq.get(
            url=req,
            headers={"Authorization": self.get_auth_header()},
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'Failed to get all invenio records: {response.text}')

        return response.json()

    def get_all_records(self) -> list:
        rsp = self.get_response(f"{self.url}/api/records?q=access.status:open")
        ret = [rsp]

        while 'next' in rsp['links'] and rsp['links']['next'] is not '':
            rsp = self.get_response(rsp['links']['next'])
            ret.append(rsp)

        return ret

    def get_all_record_ids(self) -> list:
        pages = self.get_all_records()
        records = []
        for page in pages:
            for record in page['hits']['hits']:
                records.append(record['id'])

        return records

    def get_record_json_ld(self, record_id: str) -> dict:
        response = rq.get(
            url=f"{self.url}/api/records/{record_id}",
            headers={
                'Authorization': self.get_auth_header(),
                'accept': 'application/ld+json'
            },
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'Failed to get record\'s {record_id} ld+json metadata: {response.text}')

        return response.json()

    def get_record_full_metadata(self, record_id: str) -> dict:
        response = rq.get(
            url=f"{self.url}/api/records/{record_id}",
            headers=self.get_default_headers(),
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'Failed to get record\'s {record_id} full metadata: {response.text}')

        return response.json()

    def get_record_files(self, record_id: str) -> dict:
        response = rq.get(
            url=f"{self.url}/api/records/{record_id}/files",
            headers=self.get_default_headers(),
            verify=False
        )

        if response.status_code != 200:
            raise Exception(f'Failed to get record\'s {record_id} files: {response.text}')

        return response.json()

    def get_record_fdo(self, record_id: str) -> dict:
        record_full_metadata = self.get_record_full_metadata(record_id)
        record_files = self.get_record_files(record_id)
        record_json_ld = self.get_record_json_ld(record_id)

        if record_json_ld['@context'] != 'http://schema.org':
            raise Exception(f"Record's {record_id} metadata are in an unsupported format {record_json_ld['@context']}")

        parent_version = ''
        if 'parent' in record_full_metadata:
            if 'pids' in record_full_metadata['parent'] and 'doi' in record_full_metadata['parent']['pids'] and 'identifier' in record_full_metadata['parent']['pids']['doi']:
                parent_version = record_full_metadata['parent']['pids']['doi']['identifier']
            elif 'id' in record_full_metadata['parent']:
                parent_version = record_full_metadata['parent']['id']

        distribution = [
            {
                "url": file['links']['content'],
                "fileFormat": file['mimetype'],
                "fileSize": file['size'],
            } for file in record_files['entries']
        ]

        fdo = {
            "id": record_id,
            "fdoType": "CORDRA_PREFIX/invenio-record-type",
            "fdoProfile": "CORDRA_PREFIX/invenio-record-profile",
            "@context": {
                "schema": "http://schema.org/",
                "prov": "http://www.w3.org/ns/prov#",
                "dcterms": "http://purl.org/dc/terms/",
                "identifier": "schema:identifier",
                "name": "schema:name",
                "author": "schema:author",
                "editor": "schema:editor",
                "hasPart": "dcterms:hasPart",
                "publisher": "schema:publisher",
                "keywords": "schema:keywords",
                "datePublished": "schema:datePublished",
                "dateModified": "schema:dateModified",
                "inLanguage": "schema:inLanguage",
                "contentSize": "schema:contentSize",
                "version": "schema:version",
                "license": "schema:license",
                "description": "schema:description",
                "citation": "schema:citation",
                "url": "schema:url",
                "distribution": "schema:distribution",
                "conditionsOfAccess": "schema:conditionsOfAccess",
                "wasDerivedFrom": "prov:wasDerivedFrom",
                "CreativeWork": "schema:CreativeWork",
                "Organization": "schema:Organization",
                "Person": "schema:Person",
                "Language": "schema:Language",
                "Dataset": "schema:Dataset",
                "fileFormat": "schema:fileFormat",
                "fileSize": "schema:fileSize",
                "isVersionOf": "dcterms:isVersionOf",
              },
            "@type": record_json_ld['@type'] if '@type' in record_json_ld else '',
            "identifier": record_json_ld['identifier'] if 'identifier' in record_json_ld else '',
            "name": record_json_ld['name'] if 'name' in record_json_ld else '',
            "author": record_json_ld['author'] if 'author' in record_json_ld else [],
            "editor": record_json_ld['editor'] if 'editor' in record_json_ld else [],
            "hasPart": record_json_ld['hasPart'] if 'hasPart' in record_json_ld else [],
            "publisher": record_json_ld['publisher'] if 'publisher' in record_json_ld else {'@type': '', 'name': ''},
            "keywords": record_json_ld['keywords'] if 'keywords' in record_json_ld else '',
            "datePublished": record_json_ld['datePublished'] if 'datePublished' in record_json_ld else '',
            "dateModified": record_json_ld['dateModified'] if 'dateModified' in record_json_ld else '',
            "inLanguage": record_json_ld['inLanguage'] if 'inLanguage' in record_json_ld else {'alternateName': '', '@type': '', 'name': ''},
            "contentSize": record_json_ld['contentSize'] if 'contentSize' in record_json_ld else '',
            "version": record_json_ld['version'] if 'version' in record_json_ld else '',
            "license": record_json_ld['license'] if 'license' in record_json_ld else '',
            "description": record_json_ld['description'] if 'description' in record_json_ld else '',
            "citation": record_json_ld['citation'] if 'citation' in record_json_ld else [],
            "url": record_json_ld['url'] if 'url' in record_json_ld else '',
            "distribution": distribution,
            "conditionsOfAccess": record_full_metadata['access']['record'] if 'access' in record_full_metadata and 'record' in record_full_metadata['access'] else '',
            "wasDerivedFrom": f"{self.url}/records/{record_id}",
            "isVersionOf": parent_version
        }

        return fdo