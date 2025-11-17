"""
Spotify Player

Implements playback control for Spotify using the Spotify Web API
"""

from typing import Dict, Optional
import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.background.playback.service_players.base_player import BasePlayer


class SpotifyPlayer(BasePlayer):
    """Spotify playback implementation"""

    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.base_url = "https://api.spotify.com/v1"

    def get_service_type(self) -> ExternalServiceType:
        return ExternalServiceType.SPOTIFY

    def _get_headers(self) -> Optional[Dict]:
        """Get authorization headers"""
        token = self.get_user_token()
        if not token:
            return None

        return {"Authorization": f"Bearer {token}"}

    def play_track(self, external_track_id: str, position_ms: int = 0) -> bool:
        """Start playback of a track on Spotify"""
        headers = self._get_headers()
        if not headers:
            current_app.logger.error("No Spotify token available")
            return False

        headers["Content-Type"] = "application/json"

        # Start playback
        payload = {
            "uris": [f"spotify:track:{external_track_id}"],
            "position_ms": position_ms
        }

        try:
            response = requests.put(
                f"{self.base_url}/me/player/play",
                headers=headers,
                json=payload
            )

            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                # No active device - need to transfer playback to a device
                current_app.logger.warning("No active Spotify device found")
                return False
            else:
                current_app.logger.error(
                    f"Spotify play failed: {response.status_code} - {response.text}"
                )
                return False

        except requests.RequestException as e:
            current_app.logger.error(f"Error playing track on Spotify: {e}")
            return False

    def pause(self) -> bool:
        """Pause current playback"""
        headers = self._get_headers()
        if not headers:
            return False

        try:
            response = requests.put(
                f"{self.base_url}/me/player/pause",
                headers=headers
            )
            return response.status_code == 204
        except requests.RequestException as e:
            current_app.logger.error(f"Error pausing Spotify playback: {e}")
            return False

    def resume(self) -> bool:
        """Resume paused playback"""
        headers = self._get_headers()
        if not headers:
            return False

        try:
            response = requests.put(
                f"{self.base_url}/me/player/play",
                headers=headers
            )
            return response.status_code == 204
        except requests.RequestException as e:
            current_app.logger.error(f"Error resuming Spotify playback: {e}")
            return False

    def skip_to_next(self) -> bool:
        """Skip to next track"""
        headers = self._get_headers()
        if not headers:
            return False

        try:
            response = requests.post(
                f"{self.base_url}/me/player/next",
                headers=headers
            )
            return response.status_code == 204
        except requests.RequestException as e:
            current_app.logger.error(f"Error skipping to next on Spotify: {e}")
            return False

    def skip_to_previous(self) -> bool:
        """Skip to previous track"""
        headers = self._get_headers()
        if not headers:
            return False

        try:
            response = requests.post(
                f"{self.base_url}/me/player/previous",
                headers=headers
            )
            return response.status_code == 204
        except requests.RequestException as e:
            current_app.logger.error(f"Error skipping to previous on Spotify: {e}")
            return False

    def seek(self, position_ms: int) -> bool:
        """Seek to a specific position"""
        headers = self._get_headers()
        if not headers:
            return False

        try:
            response = requests.put(
                f"{self.base_url}/me/player/seek",
                headers=headers,
                params={"position_ms": position_ms}
            )
            return response.status_code == 204
        except requests.RequestException as e:
            current_app.logger.error(f"Error seeking on Spotify: {e}")
            return False

    def set_volume(self, volume_percent: int) -> bool:
        """Set playback volume"""
        headers = self._get_headers()
        if not headers:
            return False

        # Clamp volume to 0-100
        volume_percent = max(0, min(100, volume_percent))

        try:
            response = requests.put(
                f"{self.base_url}/me/player/volume",
                headers=headers,
                params={"volume_percent": volume_percent}
            )
            return response.status_code == 204
        except requests.RequestException as e:
            current_app.logger.error(f"Error setting Spotify volume: {e}")
            return False

    def get_playback_state(self) -> Optional[Dict]:
        """Get current playback state"""
        headers = self._get_headers()
        if not headers:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/me/player",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()

                # Extract relevant information
                if data and data.get("item"):
                    track = data["item"]
                    return {
                        "is_playing": data.get("is_playing", False),
                        "progress_ms": data.get("progress_ms", 0),
                        "track_id": track.get("id"),
                        "track_name": track.get("name"),
                        "artist_name": track["artists"][0]["name"] if track.get("artists") else None,
                        "duration_ms": track.get("duration_ms", 0),
                        "device_name": data.get("device", {}).get("name"),
                        "volume_percent": data.get("device", {}).get("volume_percent"),
                    }
                elif response.status_code == 204:
                    # No active playback
                    return {"is_playing": False}

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error getting Spotify playback state: {e}")
            return None

    def add_to_queue(self, external_track_id: str) -> bool:
        """Add track to Spotify queue"""
        headers = self._get_headers()
        if not headers:
            return False

        try:
            response = requests.post(
                f"{self.base_url}/me/player/queue",
                headers=headers,
                params={"uri": f"spotify:track:{external_track_id}"}
            )
            return response.status_code == 204
        except requests.RequestException as e:
            current_app.logger.error(f"Error adding to Spotify queue: {e}")
            return False

    def get_available_devices(self) -> Optional[list]:
        """Get list of available Spotify devices"""
        headers = self._get_headers()
        if not headers:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/me/player/devices",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("devices", [])

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error getting Spotify devices: {e}")
            return None

    def transfer_playback(self, device_id: str, play: bool = True) -> bool:
        """
        Transfer playback to a specific device

        Args:
            device_id: Spotify device ID
            play: Whether to start playback after transfer

        Returns:
            True if successful
        """
        headers = self._get_headers()
        if not headers:
            return False

        headers["Content-Type"] = "application/json"

        payload = {
            "device_ids": [device_id],
            "play": play
        }

        try:
            response = requests.put(
                f"{self.base_url}/me/player",
                headers=headers,
                json=payload
            )
            return response.status_code == 204
        except requests.RequestException as e:
            current_app.logger.error(f"Error transferring Spotify playback: {e}")
            return False
