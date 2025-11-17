"""
Apple Music Player

Implements playback for Apple Music using MusicKit.
Note: Apple Music requires client-side MusicKit JS for playback control.
"""

from typing import Dict, Optional
import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.background.playback.service_players.base_player import BasePlayer


class AppleMusicPlayer(BasePlayer):
    """Apple Music playback implementation"""

    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.base_url = "https://api.music.apple.com/v1"

    def get_service_type(self) -> ExternalServiceType:
        return ExternalServiceType.APPLE

    def supports_playback_control(self) -> bool:
        """
        Apple Music requires client-side MusicKit JS for playback.
        Server-side playback control is not fully supported.
        """
        return False

    def _get_headers(self) -> Optional[Dict]:
        """Get authorization headers"""
        token = self.get_user_token()
        if not token:
            return None

        return {
            "Authorization": f"Bearer {token}",
            "Music-User-Token": token  # Apple Music uses music user token
        }

    def play_track(self, external_track_id: str, position_ms: int = 0) -> bool:
        """
        Start playback - requires MusicKit JS

        Apple Music playback is controlled via MusicKit JS on the client side.
        """
        current_app.logger.warning(
            "Apple Music playback requires client-side MusicKit JS"
        )
        return False

    def pause(self) -> bool:
        """Pause - requires MusicKit JS"""
        return False

    def resume(self) -> bool:
        """Resume - requires MusicKit JS"""
        return False

    def skip_to_next(self) -> bool:
        """Skip to next - requires MusicKit JS"""
        return False

    def skip_to_previous(self) -> bool:
        """Skip to previous - requires MusicKit JS"""
        return False

    def seek(self, position_ms: int) -> bool:
        """Seek - requires MusicKit JS"""
        return False

    def set_volume(self, volume_percent: int) -> bool:
        """Set volume - requires MusicKit JS"""
        return False

    def get_playback_state(self) -> Optional[Dict]:
        """
        Get playback state - not available via server API

        MusicKit JS maintains playback state on the client side.
        """
        return None

    def add_to_queue(self, external_track_id: str) -> bool:
        """Add to queue - requires MusicKit JS"""
        return False

    def get_track_info(self, external_track_id: str, storefront: str = "us") -> Optional[Dict]:
        """
        Get track information from Apple Music

        Args:
            external_track_id: Apple Music track ID
            storefront: Country storefront (default: us)

        Returns:
            Track information dict or None
        """
        headers = self._get_headers()
        if not headers:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/catalog/{storefront}/songs/{external_track_id}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    return data["data"][0]

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error getting Apple Music track info: {e}")
            return None

    def get_album_info(self, album_id: str, storefront: str = "us") -> Optional[Dict]:
        """
        Get album information

        Args:
            album_id: Apple Music album ID
            storefront: Country storefront

        Returns:
            Album information dict or None
        """
        headers = self._get_headers()
        if not headers:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/catalog/{storefront}/albums/{album_id}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    return data["data"][0]

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error getting Apple Music album info: {e}")
            return None

    def search(self, query: str, types: list = None, storefront: str = "us", limit: int = 10) -> Optional[Dict]:
        """
        Search Apple Music catalog

        Args:
            query: Search query
            types: List of types to search (songs, albums, artists)
            storefront: Country storefront
            limit: Maximum results per type

        Returns:
            Search results or None
        """
        headers = self._get_headers()
        if not headers:
            return None

        if types is None:
            types = ["songs"]

        params = {
            "term": query,
            "types": ",".join(types),
            "limit": limit
        }

        try:
            response = requests.get(
                f"{self.base_url}/catalog/{storefront}/search",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                return response.json()

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error searching Apple Music: {e}")
            return None
