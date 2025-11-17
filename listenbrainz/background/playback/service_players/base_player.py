"""
Base Player

Abstract base class for service-specific playback implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.db import external_service_oauth as db_oauth


class BasePlayer(ABC):
    """
    Abstract base class for service-specific players
    """

    def __init__(self, user_id: int):
        """
        Initialize player for a user

        Args:
            user_id: The ListenBrainz user ID
        """
        self.user_id = user_id

    @abstractmethod
    def get_service_type(self) -> ExternalServiceType:
        """
        Get the service type for this player

        Returns:
            ExternalServiceType enum value
        """
        pass

    def get_user_token(self) -> Optional[str]:
        """
        Get OAuth access token for the user

        Returns:
            Access token or None if not available
        """
        try:
            token_data = db_oauth.get_token(
                self.user_id,
                self.get_service_type()
            )

            if not token_data:
                return None

            return token_data.get("access_token")
        except Exception as e:
            current_app.logger.error(
                f"Error fetching token for {self.get_service_type()}: {e}"
            )
            return None

    @abstractmethod
    def play_track(self, external_track_id: str, position_ms: int = 0) -> bool:
        """
        Start playback of a track

        Args:
            external_track_id: Track ID in the external service
            position_ms: Starting position in milliseconds

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def pause(self) -> bool:
        """
        Pause current playback

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def resume(self) -> bool:
        """
        Resume paused playback

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def skip_to_next(self) -> bool:
        """
        Skip to next track

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def skip_to_previous(self) -> bool:
        """
        Skip to previous track

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def seek(self, position_ms: int) -> bool:
        """
        Seek to a specific position

        Args:
            position_ms: Position in milliseconds

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def set_volume(self, volume_percent: int) -> bool:
        """
        Set playback volume

        Args:
            volume_percent: Volume level (0-100)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_playback_state(self) -> Optional[Dict]:
        """
        Get current playback state

        Returns:
            Dict with playback information or None
        """
        pass

    @abstractmethod
    def add_to_queue(self, external_track_id: str) -> bool:
        """
        Add track to playback queue

        Args:
            external_track_id: Track ID in the external service

        Returns:
            True if successful, False otherwise
        """
        pass

    def supports_playback_control(self) -> bool:
        """
        Check if this service supports direct playback control

        Some services may not support remote playback control
        via their API and require client-side SDKs.

        Returns:
            True if playback control is supported
        """
        return True

    def get_player_info(self) -> Dict:
        """
        Get information about this player

        Returns:
            Dict with player capabilities and info
        """
        return {
            "service": self.get_service_type().value,
            "supports_playback_control": self.supports_playback_control(),
            "requires_client_sdk": not self.supports_playback_control(),
        }
