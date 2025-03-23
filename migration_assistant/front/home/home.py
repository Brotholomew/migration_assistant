import base64
import json
import os
from http import HTTPStatus
from flask import Blueprint, render_template, current_app, request
import requests as rq

from migration_assistant.migration.cordra import Cordra
from migration_assistant.migration.invenio import Invenio
from migration_assistant.utils import delete_trailing_slash
from flask_cors import cross_origin
from sqlalchemy import custom_op

from migration_assistant.repository.mapping import *
from migration_assistant.repository.setting import *

bp = Blueprint('home', __name__)

def get_recent_log() -> str | None:
    files = [file for file in os.listdir(current_app.instance_path) if file.endswith('.log')]
    if len(files) == 0:
        return None

    files.sort()
    return files[-1].replace('.log', '')

## f"{datetime.datetime.today().strftime('%Y-%m-%d::%H:%M:%S')}"

@bp.route('/')
def home():
    settings = get_setting()
    recent_log = get_recent_log()
    log_contents = None

    if recent_log:
        with open(os.path.join(current_app.instance_path, f"{recent_log}.log"), 'r') as f:
            log_contents = f.read()

    show_settings = settings is None
    show_migration = recent_log is None and not show_settings
    show_metadata = not show_settings and not show_migration

    props = {
        "settings_accordion": {
            "div_class": "show" if show_settings else "",
            "btn_class": "" if show_settings else "collapsed",
            "btn_aria": "true" if show_settings else "false",
        },
        "migration_accordion": {
            "div_class": "show" if show_migration else "",
            "btn_class": "" if show_migration else "collapsed",
            "btn_aria": "true" if show_migration else "false",
        },
        "metadata_accordion": {
            "div_class": "show" if show_metadata else "",
            "btn_class": "" if show_metadata else "collapsed",
            "btn_aria": "true" if show_metadata else "false",
        },
        "settings": settings,
        "recent_log": recent_log,
        "log_contents": log_contents
    }

    return render_template(
        'home.html',
        props=props
    )


@bp.route('/settings', methods=['POST'])
def save_settings():
    mandatory_fields = ['invenioAddress', 'invenioToken', 'cordraAddress', 'cordraUsername', 'cordraPassword']
    for field in mandatory_fields:
        if field not in request.json:
            return current_app.response_class(status=HTTPStatus.BAD_REQUEST, mimetype='application/json', response={'message': f'{field} is missing in the requests body'})

    current_app.logger.info(f"saving settings:\n - {request.json['invenioAddress']}\n - {request.json['invenioToken']}\n - {request.json['cordraAddress']}\n - {request.json['cordraUsername']}\n - {request.json['cordraPassword']}")
    settings = set_settings(
        invenio_address=delete_trailing_slash(request.json['invenioAddress']),
        invenio_token=request.json['invenioToken'],
        cordra_address=delete_trailing_slash(request.json['cordraAddress']),
        cordra_username=request.json['cordraUsername'],
        cordra_password=request.json['cordraPassword']
    )

    if settings is None:
        return current_app.response_class(status=HTTPStatus.INTERNAL_SERVER_ERROR, mimetype='application/json', response={"message": "failed to save settings in the db"})

    return current_app.response_class(status=HTTPStatus.OK, mimetype='application/json')


@bp.route('/check-connection/<service>', methods=['POST'])
def check_connection(service: str):
    if service == 'cordra':
        for field in ['url', 'username', 'password']:
            if field not in request.json:
                return current_app.response_class(status=HTTPStatus.BAD_REQUEST, mimetype='application/json', response={'message': f'missing {field} in request\'s body'})

        url = delete_trailing_slash(request.json['url'])
        try:
            r = rq.post(
                url=f'{url}/cordra/doip/20.DOIP/Op.Auth.Token?targetId=service',
                headers={
                    'Content-Type': 'application/json'
                },
                json={
                    "grant_type": "password",
                    "username": f"{request.json['username']}",
                    "password": f"{request.json['password']}"
                },
                verify=False # TODO: remove
            )
        except Exception as e:
            return current_app.response_class(status=HTTPStatus.INTERNAL_SERVER_ERROR, mimetype='application/json', response={'message': e})

        return current_app.response_class(status=r.status_code, mimetype='application/json',
                                          response={'message': r.text})
    elif service == 'invenio':
        for field in ['url', 'token']:
            if field not in request.json:
                return current_app.response_class(status=HTTPStatus.BAD_REQUEST, mimetype='application/json',
                                                  response={'message': f'missing {field} in request\'s body'})

        url = delete_trailing_slash(request.json['url'])
        try:
            r = rq.get(
                url=f'{url}/api/users',
                headers={
                    'Authorization': f'Bearer {request.json['token']}',
                    'Content-Type': 'application/json'
                },
                verify=False # TODO: remove
            )
        except Exception as e:
            return current_app.response_class(status=HTTPStatus.INTERNAL_SERVER_ERROR, mimetype='application/json', response={'message': e})

        return current_app.response_class(status=r.status_code, mimetype='application/json', response={'message': r.text})
    else:
        return current_app.response_class(status=HTTPStatus.INTERNAL_SERVER_ERROR, mimetype='application/json', response={"message": "invalid service"})


@bp.route('/metadata/<id>', methods=['GET'])
def get_metadata(id: str):
    cordra = Cordra(get_setting())
    invenio = Invenio(get_setting())

    fdo = cordra.object_present(id)
    if fdo is None:
        return current_app.response_class(status=HTTPStatus.NOT_FOUND, mimetype='application/json', response={'message': f'record: {id} has not been migrated'})
    else:
        fdo = fdo['attributes']['content']

    if 'application/ld+json' in request.accept_mimetypes.values():
        return fdo

    #if 'application/xml' in request.accept_mimetypes.values():
    #    if len(fdo['hasPart']) > 0:
    #        has_part = ""
    #        for part in fdo['hasPart']:
    #            if "@id" in part:
    #                has_part += f"<dcterms:hasPart>{part['@id']}</dcterms:hasPart>\n"
    #        return current_app.response_class(status=HTTPStatus.OK, mimetype='application/xml', response=f"""
    #        <?xml version='1.0' encoding='utf-8'?>
    #        <oai_dc:dc xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
    #          {has_part}
    #        </oai_dc:dc>
    #        """)

    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{id}</title>
        </head>
        <script type="application/ld+json">
            {json.dumps(fdo)}
        </script>
        <body>
            {json.dumps(fdo)}
        </body>
        </html>
    """