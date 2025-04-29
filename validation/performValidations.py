from flask import jsonify


def perform_validations(validations):
    for validator, args in validations:
        valid, error_msg = validator(*args)
        if not valid:
            return jsonify({"error": error_msg}), 400
    return None
