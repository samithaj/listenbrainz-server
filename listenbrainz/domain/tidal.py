import time
import base64
from typing import Sequence, Optional

import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.db import external_service_oauth
from listenbrainz.domain.external_service import (
    ExternalService,
    ExternalServiceError,
    ExternalServiceAPIError,
    ExternalServiceInvalidGrantError
)
from listenbrainz.webserver import db_conn

TIDAL_OAUTH_TOKEN_URL = 'https://auth.tidal.com/v1/oauth2/token'
TIDAL_OAUTH_AUTHORIZE_URL = 'https://login.tidal.com/authorize'

TIDAL_SCOPES = [
    'r_usr',  # Read user profile
    'w_usr',  # Write user profile
    'w_sub'  # Manage subscription
]


def _get_tidal_token(grant_type: str, token: str, code_verifier: Optional[str] = None) -> requests.Response:
    """Fetch access token or refresh token from Tidal auth API

    Args:
        grant_type (str): should be "authorization_code" to retrieve access token
                         and "refresh_token" to refresh tokens
        token (str): authorization code to retrieve access token first time
                    and refresh token to refresh access tokens
        code_verifier (str): PKCE code verifier (required for authorization_code grant)

    Returns:
        response from the Tidal authentication endpoint
    """
    client_id = current_app.config['TIDAL_CLIENT_ID']
    client_secret = current_app.config['TIDAL_CLIENT_SECRET']

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': grant_type,
    }

    if grant_type == "authorization_code":
        payload['code'] = token
        payload['redirect_uri'] = current_app.config['TIDAL_CALLBACK_URL']
        if code_verifier:
            payload['code_verifier'] = code_verifier
    elif grant_type == "refresh_token":
        payload['refresh_token'] = token

    return requests.post(TIDAL_OAUTH_TOKEN_URL, data=payload, verify=True)


class TidalService(ExternalService):
    """Service for Tidal music streaming integration"""

    def __init__(self):
        super(TidalService, self).__init__(ExternalServiceType.TIDAL)
        self.client_id = current_app.config.get('TIDAL_CLIENT_ID')
        self.client_secret = current_app.config.get('TIDAL_CLIENT_SECRET')
        self.redirect_url = current_app.config.get('TIDAL_CALLBACK_URL')

    def get_user(self, user_id: int, refresh: bool = False) -> Optional[dict]:
        """Get user token from database, optionally refreshing if expired

        Args:
            user_id: the ListenBrainz row ID of the user
            refresh: whether to refresh the token if expired

        Returns:
            User token dict or None if not found
        """
        user = external_service_oauth.get_token(db_conn, user_id, self.service)
        if user and refresh and self.user_oauth_token_has_expired(user):
            user = self.refresh_access_token(user['user_id'], user['refresh_token'])
        return user

    def add_new_user(self, user_id: int, token: dict) -> bool:
        """Create a Tidal row for a user based on OAuth access tokens

        Args:
            user_id: A flask auth `current_user.id`
            token: OAuth token response from Tidal

        Returns:
            True if user was successfully added
        """
        access_token = token['access_token']
        refresh_token = token.get('refresh_token')
        expires_at = int(time.time()) + token.get('expires_in', 3600)
        scopes = token.get('scope', '').split() if token.get('scope') else TIDAL_SCOPES

        # Get Tidal user ID
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get('https://api.tidal.com/v1/users/me', headers=headers)

            if response.status_code != 200:
                current_app.logger.error(f"Failed to get Tidal user details: {response.status_code}")
                raise ExternalServiceAPIError("Failed to get Tidal user details")

            user_details = response.json()
            external_user_id = str(user_details.get('userId') or user_details.get('id'))

        except requests.RequestException as e:
            current_app.logger.error(f"Error fetching Tidal user details: {e}")
            raise ExternalServiceAPIError(f"Error fetching Tidal user details: {e}")

        external_service_oauth.save_token(
            db_conn=db_conn,
            user_id=user_id,
            service=self.service,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_ts=expires_at,
            record_listens=False,  # Tidal doesn't support listen import yet
            scopes=scopes,
            external_user_id=external_user_id
        )

        return True

    def get_authorize_url(self, scopes: Sequence[str], state: Optional[str] = None) -> str:
        """Get the OAuth authorization URL for Tidal

        Args:
            scopes: List of OAuth scopes to request
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        scope_str = ' '.join(scopes or TIDAL_SCOPES)

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_url,
            'scope': scope_str,
        }

        if state:
            params['state'] = state

        query_string = '&'.join([f'{k}={requests.utils.quote(str(v))}' for k, v in params.items()])
        return f'{TIDAL_OAUTH_AUTHORIZE_URL}?{query_string}'

    def fetch_access_token(self, code: str, code_verifier: Optional[str] = None) -> dict:
        """Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth callback
            code_verifier: PKCE code verifier if used

        Returns:
            Token dict with access_token, refresh_token, etc.
        """
        try:
            response = _get_tidal_token('authorization_code', code, code_verifier)

            if response.status_code != 200:
                current_app.logger.error(f"Tidal token exchange failed: {response.status_code} - {response.text}")
                raise ExternalServiceAPIError(f"Failed to fetch Tidal access token: {response.status_code}")

            return response.json()

        except requests.RequestException as e:
            current_app.logger.error(f"Error during Tidal token exchange: {e}")
            raise ExternalServiceAPIError(f"Error during Tidal token exchange: {e}")

    def refresh_access_token(self, user_id: int, refresh_token: str) -> dict:
        """Refresh an expired access token

        Args:
            user_id: the ListenBrainz row ID of the user
            refresh_token: the refresh token

        Returns:
            Updated user token dict
        """
        try:
            response = _get_tidal_token('refresh_token', refresh_token)

            if response.status_code == 400:
                error_data = response.json()
                if error_data.get('error') == 'invalid_grant':
                    raise ExternalServiceInvalidGrantError("User revoked Tidal authorization")

            if response.status_code != 200:
                current_app.logger.error(f"Tidal token refresh failed: {response.status_code} - {response.text}")
                raise ExternalServiceAPIError(f"Failed to refresh Tidal token: {response.status_code}")

            token_data = response.json()
            access_token = token_data['access_token']
            new_refresh_token = token_data.get('refresh_token', refresh_token)
            expires_at = int(time.time()) + token_data.get('expires_in', 3600)

            external_service_oauth.update_token(
                db_conn=db_conn,
                user_id=user_id,
                service=self.service,
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_at=expires_at
            )

            return external_service_oauth.get_token(db_conn, user_id, self.service)

        except requests.RequestException as e:
            current_app.logger.error(f"Error during Tidal token refresh: {e}")
            raise ExternalServiceAPIError(f"Error during Tidal token refresh: {e}")

    def get_user_connection_details(self, user_id: int) -> Optional[dict]:
        """Get connection details for a user

        Args:
            user_id: the ListenBrainz row ID of the user

        Returns:
            Dict with connection details or None
        """
        user = self.get_user(user_id)
        if not user:
            return None

        return {
            'service': 'tidal',
            'external_user_id': user.get('external_user_id'),
            'scopes': user.get('scopes', []),
            'connected_at': user.get('last_updated'),
        }
