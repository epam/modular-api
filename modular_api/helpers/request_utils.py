import json

import bottle


def safe_read_json(req) -> dict | None:
    """
    Read JSON body from a Bottle request bypassing MEMFILE_MAX limit.

    bottle's ``request.json`` internally calls ``_get_body_string(MEMFILE_MAX)``
    which raises ``HTTPError(413)`` when Content-Length exceeds the limit.

    This function reads from ``request.body`` (a file-like object that is
    either a ``BytesIO`` or a temporary file) directly - no size check.

    Returns parsed dict/list or None if body is empty or not JSON.
    Raises bottle.HTTPError(400) if body contains invalid JSON.
    """
    ctype = req.content_type
    if not ctype:
        return None
    ctype = ctype.lower().split(';')[0].strip()
    if ctype not in ('application/json', 'application/json-rpc'):
        return None

    body = req.body.read()
    req.body.seek(0)  # rewind so others can read again

    if not body:
        return None

    try:
        return json.loads(body)
    except (ValueError, TypeError):
        raise bottle.HTTPError(400, 'Invalid JSON')
