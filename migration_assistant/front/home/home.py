import os
from http import HTTPStatus
from flask import Blueprint, render_template, current_app, request
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
    return files[-1]

@bp.route('/')
@cross_origin()
def home():
    settings = get_setting()
    recent_log = get_recent_log()

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
        "recent_log": recent_log
    }

    return render_template(
        'home.html',
        props=props,
        chuj=True
    )


@bp.route('/settings', methods=['POST'])
@cross_origin()
def save_settings():
    mandatory_fields = ['invenioAddress', 'invenioToken', 'cordraAddress', 'cordraToken']
    for field in mandatory_fields:
        if field not in request.json:
            return current_app.response_class(status=HTTPStatus.BAD_REQUEST, mimetype='application/json', response={'message': f'{field} is missing in the requests body'})

    current_app.logger.info(f"saving settings:\n - {request.json['invenioAddress']}\n - {request.json['invenioToken']}\n - {request.json['cordraAddress']}\n - {request.json['cordraToken']}")
    settings = set_settings(
        invenio_address=request.json['invenioAddress'],
        invenio_token=request.json['invenioToken'],
        cordra_address=request.json['cordraAddress'],
        cordra_token=request.json['cordraToken']
    )

    if settings is None:
        return current_app.response_class(status=HTTPStatus.INTERNAL_SERVER_ERROR, mimetype='application/json', response={"message": "failed to save settings in the db"})

    return current_app.response_class(status=HTTPStatus.OK, mimetype='application/json')