import time
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

# YouTube Music uses Google OAuth
YOUTUBE_MUSIC_OAUTH_TOKEN_URL = 'https://oauth2.googleapis.com/token'
YOUTUBE_MUSIC_OAUTH_AUTHORIZE_URL = 'https://accounts.google.com/o/oauth2/v2/auth'

# YouTube Music specific scopes
YOUTUBE_MUSIC_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtubepartner',
]


def _get_youtube_music_token(grant_type: str, token: str) -> requests.Response:
    """Fetch access token or refresh token from Google OAuth API

    Args:
        grant_type (str): should be "authorization_code" to retrieve access token
                         and "refresh_token" to refresh tokens
        token (str): authorization code to retrieve access token first time
                    and refresh token to refresh access tokens

    Returns:
        response from the Google OAuth endpoint
    """
    client_id = current_app.config['YOUTUBE_MUSIC_CLIENT_ID']
    client_secret = current_app.config['YOUTUBE_MUSIC_CLIENT_SECRET']

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': grant_type,
    }

    if grant_type == "authorization_code":
        payload['code'] = token
        payload['redirect_uri'] = current_app.config['YOUTUBE_MUSIC_CALLBACK_URL']
    elif grant_type == "refresh_token":
        payload['refresh_token'] = token

    return requests.post(YOUTUBE_MUSIC_OAUTH_TOKEN_URL, data=payload, verify=True)


class YoutubeMusicService(ExternalService):
    """Service for YouTube Music streaming integration"""

    def __init__(self):
        super(YoutubeMusicService, self).__init__(ExternalServiceType.YOUTUBE_MUSIC)
        self.client_id = current_app.config.get('YOUTUBE_MUSIC_CLIENT_ID')
        self.client_secret = current_app.config.get('YOUTUBE_MUSIC_CLIENT_SECRET')
        self.redirect_url = current_app.config.get('YOUTUBE_MUSIC_CALLBACK_URL')

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
        """Create a YouTube Music row for a user based on OAuth access tokens

        Args:
            user_id: A flask auth `current_user.id`
            token: OAuth token response from Google

        Returns:
            True if user was successfully added
        """
        access_token = token['access_token']
        refresh_token = token.get('refresh_token')
        expires_at = int(time.time()) + token.get('expires_in', 3600)
        scopes = token.get('scope', '').split() if token.get('scope') else YOUTUBE_MUSIC_SCOPES

        # Get YouTube/Google user ID
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            # Use Google UserInfo API to get user ID
            response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)

            if response.status_code != 200:
                current_app.logger.error(f"Failed to get YouTube Music user details: {response.status_code}")
                raise ExternalServiceAPIError("Failed to get YouTube Music user details")

            user_details = response.json()
            external_user_id = user_details.get('id')

        except requests.RequestException as e:
            current_app.logger.error(f"Error fetching YouTube Music user details: {e}")
            raise ExternalServiceAPIError(f"Error fetching YouTube Music user details: {e}")

        external_service_oauth.save_token(
            db_conn=db_conn,
            user_id=user_id,
            service=self.service,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_ts=expires_at,
            record_listens=False,  # YouTube Music doesn't support listen import yet
            scopes=scopes,
            external_user_id=external_user_id
        )

        return True

    def get_authorize_url(self, scopes: Sequence[str], state: Optional[str] = None) -> str:
        """Get the OAuth authorization URL for YouTube Music

        Args:
            scopes: List of OAuth scopes to request
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        scope_str = ' '.join(scopes or YOUTUBE_MUSIC_SCOPES)

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_url,
            'scope': scope_str,
            'access_type': 'offline',  # Request refresh token
            'prompt': 'consent',  # Force consent screen to ensure we get refresh token
        }

        if state:
            params['state'] = state

        query_string = '&'.join([f'{k}={requests.utils.quote(str(v))}' for k, v in params.items()])
        return f'{YOUTUBE_MUSIC_OAUTH_AUTHORIZE_URL}?{query_string}'

    def fetch_access_token(self, code: str) -> dict:
        """Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Token dict with access_token, refresh_token, etc.
        """
        try:
            response = _get_youtube_music_token('authorization_code', code)

            if response.status_code != 200:
                current_app.logger.error(f"YouTube Music token exchange failed: {response.status_code} - {response.text}")
                raise ExternalServiceAPIError(f"Failed to fetch YouTube Music access token: {response.status_code}")

            return response.json()

        except requests.RequestException as e:
            current_app.logger.error(f"Error during YouTube Music token exchange: {e}")
            raise ExternalServiceAPIError(f"Error during YouTube Music token exchange: {e}")

    def refresh_access_token(self, user_id: int, refresh_token: str) -> dict:
        """Refresh an expired access token

        Args:
            user_id: the ListenBrainz row ID of the user
            refresh_token: the refresh token

        Returns:
            Updated user token dict
        """
        try:
            response = _get_youtube_music_token('refresh_token', refresh_token)

            if response.status_code == 400:
                error_data = response.json()
                if error_data.get('error') == 'invalid_grant':
                    raise ExternalServiceInvalidGrantError("User revoked YouTube Music authorization")

            if response.status_code != 200:
                current_app.logger.error(f"YouTube Music token refresh failed: {response.status_code} - {response.text}")
                raise ExternalServiceAPIError(f"Failed to refresh YouTube Music token: {response.status_code}")

            token_data = response.json()
            access_token = token_data['access_token']
            # Google doesn't always return a new refresh token on refresh
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
            current_app.logger.error(f"Error during YouTube Music token refresh: {e}")
            raise ExternalServiceAPIError(f"Error during YouTube Music token refresh: {e}")

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
            'service': 'youtube_music',
            'external_user_id': user.get('external_user_id'),
            'scopes': user.get('scopes', []),
            'connected_at': user.get('last_updated'),
        }
