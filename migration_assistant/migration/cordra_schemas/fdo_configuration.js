const cordraUtil = require('cordra-util');
const cordra = require('cordra');

exports.methods = {};
exports.methods.validate = beforeSchemaValidation;
exports.beforeSchemaValidation = beforeSchemaValidation;

const FDO_REF_PREFIX = "FDO_REF"

function resolveFdoReferences(obj) {
    if (typeof obj !== 'object' || obj === null) return;

    // try to resolve all the strings
    for (let prop in obj) {
        if (typeof obj[prop] !== 'string') { continue; }
        if (!obj[prop].includes(`${FDO_REF_PREFIX}:`)) {continue; }

        let referencedObjectId = obj[prop].replace(`${FDO_REF_PREFIX}:`, '');
        let referencedObject = cordra.get(referencedObjectId);

        if (referencedObject == null) { throw `could not resolve reference: ${obj[prop]}` }
        obj[prop] = referencedObject.content.schema;
    }

    for (let prop in obj) { resolveFdoReferences(obj[prop]) }
}

function beforeSchemaValidation(object, context) {
    // NOP for special objects
    if (typeof object.content.fdoProfile !== 'string') {
        return object;
    }

    // retrieve FDO's profile
    let profile = cordra.get(object.content.fdoProfile);
    if (profile == null) {
        throw `unknown profile: ${object.content.fdoProfile}`;
    }

    let schema = JSON.parse(JSON.stringify(profile.content.schema));
    resolveFdoReferences(schema);

    let rsp = cordraUtil.validateWithSchema(object.content, schema);
    if (rsp.success == false) {
        throw `object definition is not valid with regard to its profile: ${rsp.errors[0].message}`;
    }

    // if the object contains a schema, validate the schema
    if (object.content.schema) {
        schema = JSON.parse(JSON.stringify(object.content.schema));
        resolveFdoReferences(schema);
    }

    return object;
}