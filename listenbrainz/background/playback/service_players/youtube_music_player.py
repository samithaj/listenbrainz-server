"""
YouTube Music Player

Implements playback for YouTube Music.
Note: YouTube Music requires client-side iframe player for playback.
"""

from typing import Dict, Optional
import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.background.playback.service_players.base_player import BasePlayer


class YoutubeMusicPlayer(BasePlayer):
    """YouTube Music playback implementation"""

    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def get_service_type(self) -> ExternalServiceType:
        return ExternalServiceType.YOUTUBE_MUSIC

    def supports_playback_control(self) -> bool:
        """
        YouTube Music requires client-side iframe player.
        Server-side playback control is not supported.
        """
        return False

    def _get_headers(self) -> Optional[Dict]:
        """Get authorization headers"""
        token = self.get_user_token()
        if not token:
            return None

        return {"Authorization": f"Bearer {token}"}

    def play_track(self, external_track_id: str, position_ms: int = 0) -> bool:
        """
        Start playback - requires client-side iframe player

        YouTube Music uses the YouTube iframe player API for playback,
        which must be controlled from the client side.
        """
        current_app.logger.warning(
            "YouTube Music playback requires client-side iframe player"
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
        """Get playback state - not supported via API"""
        return None

    def add_to_queue(self, external_track_id: str) -> bool:
        """Add to queue - requires client SDK"""
        return False

    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """
        Get video/track information from YouTube

        Args:
            video_id: YouTube video ID

        Returns:
            Video information dict or None
        """
        headers = self._get_headers()
        if not headers:
            return None

        params = {
            "part": "snippet,contentDetails",
            "id": video_id
        }

        try:
            response = requests.get(
                f"{self.base_url}/videos",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    return data["items"][0]

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error getting YouTube video info: {e}")
            return None

    def get_embed_url(self, video_id: str, autoplay: bool = False) -> str:
        """
        Get YouTube embed URL for client-side playback

        Args:
            video_id: YouTube video ID
            autoplay: Whether to autoplay

        Returns:
            Embed URL
        """
        autoplay_param = "1" if autoplay else "0"
        return f"https://www.youtube.com/embed/{video_id}?autoplay={autoplay_param}&enablejsapi=1"
