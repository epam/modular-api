import secrets
import time
from datetime import timedelta

import jwt

from modular_api.helpers.exceptions import ModularApiUnauthorizedException
from modular_api.services import SP
from modular_api.web_service import META_VERSION_ID
from modular_api.services.refresh_token_service import RefreshTokenService

SESSION_TOKEN_EXPIRATION = int(timedelta(days=1).total_seconds())
REFRESH_TOKEN_EXPIRATION = int(timedelta(days=14).total_seconds())


def encode_data_to_jwt(username: str) -> str:
    return jwt.encode(
        payload={
            'username': username,
            'iat': int(time.time()),
            'exp': int(time.time()) + SESSION_TOKEN_EXPIRATION,
            'meta_version': META_VERSION_ID,
        },
        key=SP.env.secret_key(),
        algorithm='HS256',
    )


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            key=SP.env.secret_key(),
            algorithms='HS256',
        )
    except jwt.exceptions.ExpiredSignatureError:
        # if you are going to change text in next line - you must update
        # RELOGIN_TEXT variable in Modular-CLI to keep automated re-login
        raise ModularApiUnauthorizedException(
            'The provided token (session or refresh) has expired. '
            'Please re-authenticate to obtain new tokens'
        )
    except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
        return {}
    return payload


def username_from_jwt_token(token: str) -> str | None:
    # todo fix, sometimes this method can receive not jwt token but base64 encoded basic auth string (username:password)
    payload = decode_jwt_token(token)
    if username := payload.get('username'):
        return username


def gen_refresh_token_version() -> str:
    return secrets.token_hex()


def encode_data_to_refresh_jwt(username: str, version: str) -> str:
    return jwt.encode(
        payload={
            'username': username,
            'version': version,
            'iat': int(time.time()),
            'exp': int(time.time()) + REFRESH_TOKEN_EXPIRATION,
        },
        key=SP.env.secret_key(),
        algorithm='HS256',
    )


def validate_refresh_token(refresh_token: str) -> tuple:
    try:
        decoded_token = jwt.decode(
            refresh_token,
            key=SP.env.secret_key(),
            algorithms='HS256',
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception):
        return None, None
    # Retrieve the token details
    username = decoded_token['username']
    version = decoded_token['version']
    # Check if the token exists and is valid
    existing_token = RefreshTokenService.get_refresh_token(username)
    if not existing_token:
        return None, None
    # Retrieve the existing_token from db details
    version_from_db = existing_token.version
    # Validate if version match the database records
    if version != version_from_db:
        RefreshTokenService.delete_refresh_token(existing_token)
        return None, None

    return username, version
