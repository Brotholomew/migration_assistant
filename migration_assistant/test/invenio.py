import base64
from enum import verify

from migration_assistant.migration.invenio import Invenio
from migration_assistant.dbo.setting import Setting

import pytest
import requests
import json

INVENIO_TOKEN = "token"
INVENIO_URL = "https://invenio"

@pytest.fixture
def invenio():
    setting = Setting(
        invenio_address=INVENIO_URL,
        invenio_token=INVENIO_TOKEN,
        cordra_address = "",
        _cordra_username = "",
        _cordra_password = ""
    )
    return Invenio(setting)


def test_mimetype_accepted_valid_type(invenio, requests_mock):
    requests_mock.get(
        f"{INVENIO_URL}/api/records/non-existent",
        json={"message": "Invalid 'Accept' header. Expected one of: application/json, text/html"},
        status_code=406
    )
    assert invenio.mimetype_accepted("application/json")
    assert not invenio.mimetype_accepted("application/xml")


def test_mimetype_accepted_status_200(invenio, requests_mock):
    requests_mock.get(
        f"{INVENIO_URL}/api/records/non-existent",
        status_code=200
    )
    assert not invenio.mimetype_accepted("application/json")


def test_mimetype_accepted_no_message(invenio, requests_mock):
    requests_mock.get(
        f"{INVENIO_URL}/api/records/non-existent",
        json={},
        status_code=406
    )
    assert not invenio.mimetype_accepted("application/json")


def test_proxy_content_negotiation_with_mimetype(invenio, requests_mock):
    mock = requests_mock.get(
        f"{INVENIO_URL}/api/records/recid",
        text="record-content"
    )
    response = invenio.proxy_content_negotiation("recid", "application/ld+json")
    assert response.text == "record-content"
    assert mock.last_request.headers["Accept"] == "application/ld+json"


def test_proxy_content_negotiation_without_mimetype(invenio, requests_mock):
    mock = requests_mock.get(
        f"{INVENIO_URL}/api/records/recid",
        text="record-content"
    )
    response = invenio.proxy_content_negotiation("recid", None)
    assert response.text == "record-content"
    assert mock.last_request.headers["Accept"] == '*/*'


def test_get_response_success(invenio, requests_mock):
    requests_mock.get(f"{INVENIO_URL}/api/ok", json={"result": "ok"})
    assert invenio.get_response(f"{INVENIO_URL}/api/ok") == {"result": "ok"}


def test_get_response_failure(invenio, requests_mock):
    requests_mock.get(f"{INVENIO_URL}/api/fail", text="error", status_code=500)
    with pytest.raises(Exception, match="Failed to get all invenio records"):
        invenio.get_response(f"{INVENIO_URL}/api/fail")


def test_get_all_records_multiple_pages(invenio, requests_mock):
    requests_mock.get(
        f"{INVENIO_URL}/api/records?q=access.status:open",
        json={"hits": [], "links": {"next": f"{INVENIO_URL}/api/next"}}
    )
    requests_mock.get(
        f"{INVENIO_URL}/api/next",
        json={"hits": [], "links": {}}
    )
    records = invenio.get_all_records()
    assert len(records) == 2


def test_get_all_record_ids(invenio, requests_mock):
    requests_mock.get(
        f"{INVENIO_URL}/api/records?q=access.status:open",
        json={
            "hits": {"hits": [{"id": "rec1"}, {"id": "rec2"}]},
            "links": {}
        }
    )
    ids = invenio.get_all_record_ids()
    assert ids == ["rec1", "rec2"]


def test_get_record_json_ld_success(invenio, requests_mock):
    requests_mock.get(
        f"{INVENIO_URL}/api/records/myid",
        json={"@context": "http://schema.org"},
        headers={"Content-Type": "application/ld+json"}
    )
    assert invenio.get_record_json_ld("myid")["@context"] == "http://schema.org"


def test_get_record_json_ld_fail(invenio, requests_mock):
    requests_mock.get(f"{INVENIO_URL}/api/records/myid", text="error", status_code=404)
    with pytest.raises(Exception, match="Failed to get record's myid ld\\+json metadata"):
        invenio.get_record_json_ld("myid")


def test_get_record_full_metadata(invenio, requests_mock):
    requests_mock.get(
        f"{INVENIO_URL}/api/records/myid",
        json={"id": "myid"}
    )
    assert invenio.get_record_full_metadata("myid")["id"] == "myid"


def test_get_record_files_fail(invenio, requests_mock):
    requests_mock.get(f"{INVENIO_URL}/api/records/myid/files", status_code=404, text="not found")
    with pytest.raises(Exception, match="Failed to get record's myid files"):
        invenio.get_record_files("myid")


def test_get_record_fdo_success(invenio, requests_mock):
    # Full metadata
    requests_mock.get(f"{INVENIO_URL}/api/records/myid/files", text=json.dumps({
        "entries": [{
            "links": {"content": "https://file.com/data.txt"},
            "mimetype": "text/plain",
            "size": 1000
        }]
    }))
    requests_mock.get(
        f"{INVENIO_URL}/api/records/myid",
        text=json.dumps({
            "@context": "http://schema.org",
            "@type": "Dataset",
            "identifier": "doi:myid",
            "name": "Dataset Title",
            "parent": {
                "id": "parent-id"
            }
        })
    )

    fdo = invenio.get_record_fdo("myid")
    assert fdo["id"] == "myid"
    assert fdo["distribution"][0]["fileFormat"] == "text/plain"
    assert fdo["isVersionOf"] == "parent-id"


def test_get_record_fdo_invalid_context(invenio, requests_mock):
    requests_mock.get(f"{INVENIO_URL}/api/records/myid/files", text="{\"entries\": []}")
    requests_mock.get(
        f"{INVENIO_URL}/api/records/myid",
        text="{\"@context\": \"incorrect\"}"
    )

    with pytest.raises(Exception):
        invenio.get_record_fdo("myid")
