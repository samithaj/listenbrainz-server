"""
Tidal Player

Implements playback control for Tidal
Note: Tidal's API has limited playback control capabilities.
Most playback features require the Tidal client SDK.
"""

from typing import Dict, Optional
import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.background.playback.service_players.base_player import BasePlayer


class TidalPlayer(BasePlayer):
    """Tidal playback implementation"""

    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.base_url = "https://api.tidal.com/v1"

    def get_service_type(self) -> ExternalServiceType:
        return ExternalServiceType.TIDAL

    def supports_playback_control(self) -> bool:
        """
        Tidal requires client-side SDK for playback control.
        Server-side API has limited playback capabilities.
        """
        return False

    def _get_headers(self) -> Optional[Dict]:
        """Get authorization headers"""
        token = self.get_user_token()
        if not token:
            return None

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def play_track(self, external_track_id: str, position_ms: int = 0) -> bool:
        """
        Start playback - requires client SDK

        This method returns False as server-side playback control
        is not supported by Tidal's API.
        """
        current_app.logger.warning(
            "Tidal playback requires client-side SDK integration"
        )
        return False

    def pause(self) -> bool:
        """Pause - requires client SDK"""
        return False

    def resume(self) -> bool:
        """Resume - requires client SDK"""
        return False

    def skip_to_next(self) -> bool:
        """Skip to next - requires client SDK"""
        return False

    def skip_to_previous(self) -> bool:
        """Skip to previous - requires client SDK"""
        return False

    def seek(self, position_ms: int) -> bool:
        """Seek - requires client SDK"""
        return False

    def set_volume(self, volume_percent: int) -> bool:
        """Set volume - requires client SDK"""
        return False

    def get_playback_state(self) -> Optional[Dict]:
        """
        Get playback state - not supported via API

        Returns None as Tidal doesn't provide playback state via API
        """
        return None

    def add_to_queue(self, external_track_id: str) -> bool:
        """Add to queue - requires client SDK"""
        return False

    def get_track_url(self, external_track_id: str) -> Optional[str]:
        """
        Get streaming URL for a track

        This can be used for client-side playback

        Args:
            external_track_id: Tidal track ID

        Returns:
            Streaming URL or None
        """
        headers = self._get_headers()
        if not headers:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/tracks/{external_track_id}/streamUrl",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("url")

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error getting Tidal stream URL: {e}")
            return None

    def get_track_info(self, external_track_id: str) -> Optional[Dict]:
        """
        Get track information

        Args:
            external_track_id: Tidal track ID

        Returns:
            Track information dict or None
        """
        headers = self._get_headers()
        if not headers:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/tracks/{external_track_id}",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error getting Tidal track info: {e}")
            return None
