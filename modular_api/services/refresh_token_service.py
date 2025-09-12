from typing import Optional
from modular_api.helpers.log_helper import get_logger
from modular_api.models.refresh_token_model import RefreshToken

_LOG = get_logger(__name__)


class RefreshTokenService:
    @staticmethod
    def create_and_save(
            username: str,
            version: str,
    ) -> RefreshToken:
        _LOG.info("Creating and saving refresh token")
        refresh_token = RefreshToken(username=username, version=version)
        refresh_token.save()
        return refresh_token

    @staticmethod
    def get_refresh_token(username: str) -> Optional[RefreshToken]:
        _LOG.info(f"Retrieving refresh token for user '{username}'")
        try:
            return RefreshToken.get_nullable(hash_key=username)
        except RefreshToken.DoesNotExist:
            _LOG.warning(f"Refresh token for user '{username}' does not exist")
            return None

    @staticmethod
    def delete_refresh_token(refresh_token: RefreshToken) -> None:
        _LOG.info(f"Deleting refresh token for user '{refresh_token.username}'")
        refresh_token.delete()
