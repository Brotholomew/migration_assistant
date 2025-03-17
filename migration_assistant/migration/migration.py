from sys import prefix
from migration_assistant.migration.cordra import Cordra
from migration_assistant.migration.migration_logger import MigrationLogger
from migration_assistant.repository.setting import *
from simple_websocket import Server
import os
from migration_assistant.migration.cordra_schemas import CORDRA_SCHEMAS_DIR
import json


def parse_files(*, prefix = '', exclude='') -> dict:
    filenames = [file for file in os.listdir(CORDRA_SCHEMAS_DIR) if file.startswith(prefix) and (exclude == '' or exclude not in file) and file.endswith('.json')]
    files = {filename.replace('_', '-').replace('fdo', 'FDO').replace('.json', ''): f"{CORDRA_SCHEMAS_DIR}/{filename}" for filename in filenames}
    return files

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def migrate(ws: Server):
    cordra = Cordra(get_setting())
    logger = MigrationLogger(ws)
    base_fdos = parse_files(prefix='fdo')
    fdos = parse_files(exclude='fdo')
    force_update = False

    # extract the base fdo schema
    fdo_configuration_json_filename = base_fdos['FDO-configuration']
    fdo_configuration_js_filename = base_fdos['FDO-configuration'].replace('.json', '.js')
    fdo_configuration_pure_json = read_file(fdo_configuration_json_filename)
    _ = base_fdos.pop('FDO-configuration')

    # check for presence of the base FDO schema
    try:
        if not cordra.schema_present('FDO-configuration'):
            # will have to create all profiles / attribute definitions at a lower level
            force_update = True
            cordra.post_schema('FDO-configuration', fdo_configuration_pure_json)
            logger.log('created the FDO-configuration schema')
        else:
            logger.log('the FDO-configuration schema is already present, skipping')
    except Exception as e:
        logger.err(f'migration failed to create the FDO-configuration schema: {e}, terminating')
        logger.end()
        return

    for fdo, filename in base_fdos.items():
        try:
            if force_update or not cordra.object_present(fdo):
                force_update = True
                json_full = read_file(filename)
                obj = json.loads(json_full)

                # remove references
                # at the beginning these objects do not exist
                obj["fdoType"] = {}
                obj["fdoProfile"] = {}
                json_no_ref = json.dumps(obj)

                cordra.create_object(fdo, json_no_ref)
                logger.log(f'created the FDO: {fdo}')
            else:
                logger.log(f'the FDO {fdo} already exists, skipping')
        except Exception as e:
            logger.err(f'migration failed to create one of the base fdo concepts {fdo}: {e}, terminating')
            logger.end()
            return

    # add the rest of the fdos without validating references (ordering does not matter)
    for fdo, filename in fdos.items():
        try:
            if not cordra.object_present(fdo):
                json_full = read_file(filename)
                cordra.create_object(fdo, json_full)
                logger.log(f'created the FDO: {fdo}')
            else:
                logger.log(f'the FDO {fdo} already exists, skipping')
        except Exception as e:
            logger.err(f'migration failed to create one of the base fdo concepts {fdo}: {e}, terminating')
            logger.end()
            return

    # update base fdos to validate references
    if force_update:
        fdo_configuration_js = read_file(fdo_configuration_js_filename)
        obj = json.loads(fdo_configuration_pure_json)
        obj['javascript'] = fdo_configuration_js
        json_full = json.dumps(obj)

        try:
            cordra.update_schema_with_js('FDO-configuration', fdo_configuration_js)
            # cordra.post_schema('FDO-configuration', json_full)
            logger.log('fully updated the FDO-configuration schema')
        except Exception as e:
            logger.err(f'failed to update the base fdos: {e}')
            logger.end()
            return

        for fdo, filename in base_fdos.items():
            try:
                json_full = read_file(filename)
                cordra.update_object(fdo, json_full)
                logger.log(f'fully updated the FDO: {fdo}')
            except Exception as e:
                logger.err(f'failed to update the {fdo}: {e}, terminating')
                logger.end()
                return

    logger.end()