import base64
from enum import verify

from migration_assistant.migration.cordra import Cordra
from migration_assistant.dbo.setting import Setting

import pytest
import requests
import json

CORDRA_USRN = "admin"
CORDRA_PASS = "admin"
CORDRA_URL = "https://cordra"

@pytest.fixture
def cordra_mock():
    set = Setting(
        invenio_address="",
        invenio_token="",
        cordra_address=CORDRA_URL,
        _cordra_username=CORDRA_USRN,
        _cordra_password=CORDRA_PASS
    )

    return Cordra(set)

def get_real_auth():
    auth_str = f"{CORDRA_USRN}:{CORDRA_PASS}"
    auth_str_bytes = auth_str.encode("utf-8")
    b64_bytes = base64.b64encode(auth_str_bytes)
    return f'Basic {b64_bytes.decode("utf-8")}'

def test_get_auth_header(cordra_mock):
    assert cordra_mock.get_auth_header() == get_real_auth()

def test_get_default_headers(cordra_mock):
    header = cordra_mock.get_default_headers()

    assert header["Content-Type"] == 'application/json'
    assert header["Authorization"] == get_real_auth()

def test_get_design_success(cordra_mock, requests_mock):
    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        headers=cordra_mock.get_default_headers(),
        text="{}"
    )

    assert cordra_mock.get_design() == {}

def test_get_design_failure(cordra_mock, requests_mock):
    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        headers=cordra_mock.get_default_headers(),
        status_code=404
    )

    with pytest.raises(Exception):
        cordra_mock.get_design()

def test_get_prefix(cordra_mock, requests_mock):
    mock_response = {"handleMintingConfig": {"prefix": "12345"}}
    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        text=json.dumps(mock_response)
    )

    assert cordra_mock.get_prefix() == "12345"

def test_schema_present_exists(cordra_mock, requests_mock):
    schema_name = "test_schema"
    mock_response = {
        "schemas": {
            "test_schema": {"type": "record"}
        }
    }

    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        text=json.dumps(mock_response)
    )

    assert cordra_mock.schema_present(schema_name) == {"type": "record"}

def test_schema_present_not_exists(cordra_mock, requests_mock):
    mock_response = {"schemas": {}}

    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        text=json.dumps(mock_response)
    )

    assert cordra_mock.schema_present("missing_schema") is None

def test_post_schema_success(cordra_mock, requests_mock):
    schema_name = "test"
    schema_content = '{"key": "value"}'
    requests_mock.put(
        url=f"{CORDRA_URL}/schemas/{schema_name}",
        status_code=200
    )

    cordra_mock.get_prefix = lambda: ""  # Patch resolve_prefix

    cordra_mock.post_schema(schema_name, schema_content)

def test_object_present_found(cordra_mock, requests_mock):
    cordra_mock.get_prefix = lambda: "12345"
    object_name = "obj1"
    expected = {"some": "data"}

    requests_mock.get(
        url=f"{CORDRA_URL}/cordra/doip/0.DOIP/Op.Retrieve?targetId=12345/{object_name}",
        json=expected,
        status_code=200
    )

    assert cordra_mock.object_present(object_name) == expected

def test_object_present_not_found(cordra_mock, requests_mock):
    cordra_mock.get_prefix = lambda: "12345"
    object_name = "obj1"

    requests_mock.get(
        url=f"{CORDRA_URL}/cordra/doip/0.DOIP/Op.Retrieve?targetId=12345/{object_name}",
        status_code=404
    )

    assert cordra_mock.object_present(object_name) is None

def test_create_object_already_exists(cordra_mock, requests_mock):
    cordra_mock.get_prefix = lambda: "12345"
    name = "obj1"
    expected = {"already": "exists"}

    requests_mock.get(
        url=f"{CORDRA_URL}/cordra/doip/0.DOIP/Op.Retrieve?targetId=12345/{name}",
        json=expected,
        status_code=200
    )

    assert cordra_mock.create_object(name, '{"some": "data"}') == expected

def test_create_object_success(cordra_mock, requests_mock):
    cordra_mock.get_prefix = lambda: "12345"
    name = "obj2"

    requests_mock.get(
        url=f"{CORDRA_URL}/cordra/doip/0.DOIP/Op.Retrieve?targetId=12345/{name}",
        status_code=404
    )
    requests_mock.post(
        url=f"{CORDRA_URL}/objects/?type=FDO-configuration&suffix={name}",
        json={"created": "yes"},
        status_code=200
    )

    result = cordra_mock.create_object(name, '{"some": "data"}')
    assert result == {"created": "yes"}

def test_update_object_creates_if_missing(cordra_mock, requests_mock):
    cordra_mock.get_prefix = lambda: "12345"
    name = "obj3"

    requests_mock.get(
        url=f"{CORDRA_URL}/cordra/doip/0.DOIP/Op.Retrieve?targetId=12345/{name}",
        status_code=404
    )
    requests_mock.post(
        url=f"{CORDRA_URL}/objects/?type=FDO-configuration&suffix={name}",
        json={"created": "yes"},
        status_code=200
    )

    result = cordra_mock.update_object(name, '{"some": "data"}')
    assert result == {"created": "yes"}

def test_update_object_success(cordra_mock, requests_mock):
    cordra_mock.get_prefix = lambda: "12345"
    name = "obj4"

    requests_mock.get(
        url=f"{CORDRA_URL}/cordra/doip/0.DOIP/Op.Retrieve?targetId=12345/{name}",
        json={"existing": "yes"},
        status_code=200
    )
    requests_mock.put(
        url=f"{CORDRA_URL}/objects/12345/{name}",
        json={"updated": "yes"},
        status_code=200
    )

    result = cordra_mock.update_object(name, '{"some": "data"}')
    assert result == {"updated": "yes"}

def test_resolve_prefix(cordra_mock):
    cordra_mock.get_prefix = lambda: "PREFIX"
    assert cordra_mock.resolve_prefix("CORDRA_PREFIX/foo") == "PREFIX/foo"

def test_update_schema_with_js_schema_not_found(cordra_mock, requests_mock):
    schema_name = "missing_schema"
    requests_mock.get(
        url=f"{CORDRA_URL}/schemas/{schema_name}",
        status_code=404
    )

    with pytest.raises(Exception, match=f"schema {schema_name} not found"):
        cordra_mock.update_schema_with_js(schema_name, "some_js()")

def test_update_schema_with_js_schema_id_missing(cordra_mock, requests_mock):
    schema_name = "schema1"
    requests_mock.get(
        url=f"{CORDRA_URL}/schemas/{schema_name}",
        status_code=200
    )

    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        json={"schemaIds": {"abc": "different_name"}}
    )

    with pytest.raises(Exception, match=f"schema {schema_name} not found"):
        cordra_mock.update_schema_with_js(schema_name, "some_js()")

def test_update_schema_with_js_full_object_fail(cordra_mock, requests_mock):
    schema_name = "schema1"
    requests_mock.get(url=f"{CORDRA_URL}/schemas/{schema_name}", status_code=200)
    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        json={"schemaIds": {"id123": schema_name}}
    )
    requests_mock.get(
        url=f"{CORDRA_URL}/objects/id123?full=true",
        status_code=404
    )

    with pytest.raises(Exception, match=f"failed to update schema: {schema_name}"):
        cordra_mock.update_schema_with_js(schema_name, "some_js()")

def test_update_schema_with_js_delete_fail(cordra_mock, requests_mock):
    schema_name = "schema1"
    requests_mock.get(url=f"{CORDRA_URL}/schemas/{schema_name}", status_code=200)
    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        json={"schemaIds": {"id123": schema_name}}
    )
    requests_mock.get(
        url=f"{CORDRA_URL}/objects/id123?full=true",
        json={"content": {}},
        status_code=200
    )
    requests_mock.delete(
        url=f"{CORDRA_URL}/schemas/{schema_name}",
        status_code=500,
        text="Internal Server Error"
    )

    with pytest.raises(Exception, match="failed to delete schema"):
        cordra_mock.update_schema_with_js(schema_name, "some_js()")

def test_update_schema_with_js_upload_fail(cordra_mock, requests_mock):
    schema_name = "schema1"
    requests_mock.get(url=f"{CORDRA_URL}/schemas/{schema_name}", status_code=200)
    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        json={"schemaIds": {"id123": schema_name}}
    )
    requests_mock.get(
        url=f"{CORDRA_URL}/objects/id123?full=true",
        json={"content": {}},
        status_code=200
    )
    requests_mock.delete(
        url=f"{CORDRA_URL}/schemas/{schema_name}",
        status_code=200
    )
    requests_mock.post(
        url=f"{CORDRA_URL}/uploadObjects",
        status_code=400,
        text="Bad request"
    )

    with pytest.raises(Exception, match="failed to update schema"):
        cordra_mock.update_schema_with_js(schema_name, "some_js()")

def test_update_schema_with_js(cordra_mock, requests_mock):
    schema_name = "schema1"
    js_code = "function test() {}"
    cordra_mock.get_prefix = lambda: "prefix"

    # GET schema endpoint
    requests_mock.get(
        url=f"{CORDRA_URL}/schemas/{schema_name}",
        status_code=200
    )

    # GET design
    requests_mock.post(
        url=f"{CORDRA_URL}/cordra/doip/20.DOIP/Op.GetDesign?targetId=service",
        json={
            "schemaIds": {
                "schema_id_123": schema_name
            }
        }
    )

    # GET full object
    full_schema = {
        "content": {},
        "id": "schema_id_123"
    }
    requests_mock.get(
        url=f"{CORDRA_URL}/objects/schema_id_123?full=true",
        json=full_schema,
        status_code=200
    )

    # DELETE old schema
    requests_mock.delete(
        url=f"{CORDRA_URL}/schemas/{schema_name}",
        status_code=200
    )

    # POST new schema
    requests_mock.post(
        url=f"{CORDRA_URL}/uploadObjects",
        json={"result": "ok"},
        status_code=200
    )

    result = cordra_mock.update_schema_with_js(schema_name, js_code)
    assert result == {"result": "ok"}
