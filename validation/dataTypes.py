import re
from typing import Literal
from urllib.parse import urlparse
from dateutil.parser import parse


from flask.json import jsonify


def validate_member_name(key: str, value, max_length=50, pattern=r"^([a-zA-Z\s'-]+)?$"):
    if not isinstance(value, str):
        return False, f"Value of {key} must be a string"
    if len(value) > max_length:
        return False, f"Value of {key} exceeds maximum length of {max_length}"
    if not re.fullmatch(pattern, value):
        return False, f"Value of {key} contains invalid characters"
    return True, ""


def validate_boolean(key: str, value):
    if not isinstance(value, bool):
        return False, f"Value of {key} must be a boolean"
    return True, ""


def validate_member_description(description, max_length=10000):
    if not isinstance(description, str):
        return False, "Description must be a string"
    if len(description) > max_length:
        return (
            False,
            f"Description exceeds maximum allowed length of {max_length} characters",
        )
    return True, ""


def validate_date_format(date_str):
    try:
        parsed_date = parse(date_str)
        return True, parsed_date
    except ValueError as e:
        return False, f"Date '{date_str}' is invalid: {str(e)}"


def validate_gender(gender):
    allowed = {"male", "female"}
    if not isinstance(gender, str):
        return False, "Gender must be a string (male or female)"
    if gender.lower() not in allowed:
        return False, "Gender must be 'male' or 'female'"
    return True, ""


def _validate_url(url):
    if not isinstance(url, str):
        return False, "URL must be a string"

    # Check if the URL is not empty
    if not url.strip():
        return False, "URL cannot be empty"

    # Parse the URL
    try:
        result = urlparse(url)
        # Check for scheme and netloc
        if all([result.scheme, result.netloc]):
            # Additional check for allowed schemes (http, https, ftp)
            if result.scheme not in ["http", "https", "ftp"]:
                return False, "URL must start with http://, https://, or ftp://"
            # Check for valid characters in the URL
            if not re.match(
                r"^[a-zA-Z0-9\-\.\_\~\:\/\?\#\[\]\@\!\$\&\'\(\)\*\+\,\;\=\%]+$", url
            ):
                return False, "URL contains invalid characters"
            return True, ""
        else:
            return False, "Invalid URL format"
    except ValueError:
        return False, "Invalid URL"


def validate_url(key: str, url):
    # Validate pic
    if url:
        valid, error_msg = _validate_url(url)
        if not valid:
            return False, f"Invalid {key} URL: {error_msg}"

    return True, ""


def validate_relation_type(relation_type: str):
    if not isinstance(relation_type, str):
        return False, "Value of relation type must be a string"
    allowed_relations = {"parent", "spouse"}
    if relation_type not in allowed_relations:
        return (
            False,
            f"Invalid relation type: {relation_type}. Must be 'parent' or 'spouse'",
        )
    return True, ""


def validate_vertex_exists(
    vertex_id: int, source_or_target: Literal["Source", "Target"], g
):
    if not isinstance(vertex_id, int):
        return False, f"Vertex id of {source_or_target} is not a number"
    if not g.V(vertex_id).hasNext():
        return False, f"{source_or_target} vertext not found!"
    return True, ""


def validate_vertex_ids_differ(source_id: int, target_id: int):
    if source_id == target_id:
        return False, f"Source and target have the same id: {source_id}"
    return True, ""
