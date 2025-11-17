"""
Playback Router

Routes playback requests to the appropriate music service based on:
- Track availability on each service
- User preferences
- Service priority
- Fallback logic
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from flask import current_app
import uuid

from data.model.external_service import ExternalServiceType
from listenbrainz.db import external_service_oauth as db_oauth


class PlaybackState(Enum):
    """Playback state enumeration"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"


class PlaybackRouter:
    """
    Routes playback requests to the best available music service
    """

    def __init__(self, user_id: int):
        """
        Initialize playback router for a user

        Args:
            user_id: The ListenBrainz user ID
        """
        self.user_id = user_id
        self.current_session_id = None
        self.current_service = None
        self.current_state = PlaybackState.STOPPED
        self.current_track = None
        self.queue = []

        # Service priority (higher = preferred)
        self.service_priority = {
            ExternalServiceType.SPOTIFY: 4,
            ExternalServiceType.TIDAL: 3,
            ExternalServiceType.APPLE: 2,
            ExternalServiceType.YOUTUBE_MUSIC: 1,
        }

    def get_user_connected_services(self) -> List[str]:
        """
        Get list of services the user has connected

        Returns:
            List of connected service names
        """
        connected = []

        try:
            # Check each service for valid OAuth token
            for service_type in [
                ExternalServiceType.SPOTIFY,
                ExternalServiceType.TIDAL,
                ExternalServiceType.APPLE,
                ExternalServiceType.YOUTUBE_MUSIC,
            ]:
                token = db_oauth.get_token(self.user_id, service_type)
                if token:
                    connected.append(service_type.value)
        except Exception as e:
            current_app.logger.error(f"Error fetching connected services: {e}")

        return connected

    def select_playback_service(
        self,
        recording_mbid: str,
        available_services: Optional[Dict[str, str]] = None,
        preferred_service: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Select the best service for playback

        Args:
            recording_mbid: MusicBrainz recording ID
            available_services: Dict of {service: external_track_id}
            preferred_service: User's preferred service (if any)

        Returns:
            Tuple of (service_name, external_track_id) or (None, None)
        """
        if not available_services:
            # Query track_service_mapping to find available services
            from listenbrainz.db import musicmatch as db_musicmatch
            available_services = db_musicmatch.get_track_services(recording_mbid)

        if not available_services:
            current_app.logger.warning(
                f"Track {recording_mbid} not available on any service"
            )
            return None, None

        # Get user's connected services
        connected_services = self.get_user_connected_services()

        # Filter to only services user has connected
        available_and_connected = {
            service: track_id
            for service, track_id in available_services.items()
            if service in connected_services
        }

        if not available_and_connected:
            current_app.logger.warning(
                f"Track {recording_mbid} not available on user's connected services"
            )
            return None, None

        # Prefer user's explicit preference
        if preferred_service and preferred_service in available_and_connected:
            return preferred_service, available_and_connected[preferred_service]

        # Select based on priority
        best_service = None
        best_priority = -1

        for service, track_id in available_and_connected.items():
            try:
                service_enum = ExternalServiceType(service)
                priority = self.service_priority.get(service_enum, 0)

                if priority > best_priority:
                    best_priority = priority
                    best_service = service
            except ValueError:
                continue

        if best_service:
            return best_service, available_and_connected[best_service]

        # Fallback: just pick the first available
        service = next(iter(available_and_connected.keys()))
        return service, available_and_connected[service]

    def create_session(self, service: str) -> str:
        """
        Create a new playback session

        Args:
            service: Service name to use for playback

        Returns:
            Session ID
        """
        from listenbrainz.db import musicmatch as db_musicmatch

        session_id = str(uuid.uuid4())

        try:
            db_musicmatch.create_playback_session(
                session_id=session_id,
                user_id=self.user_id,
                service=service
            )

            self.current_session_id = session_id
            self.current_service = service

            return session_id
        except Exception as e:
            current_app.logger.error(f"Error creating playback session: {e}")
            raise

    def end_session(self):
        """End the current playback session"""
        if not self.current_session_id:
            return

        from listenbrainz.db import musicmatch as db_musicmatch

        try:
            db_musicmatch.end_playback_session(self.current_session_id)

            self.current_session_id = None
            self.current_service = None
            self.current_state = PlaybackState.STOPPED
            self.current_track = None
        except Exception as e:
            current_app.logger.error(f"Error ending playback session: {e}")

    def add_to_queue(self, recording_mbid: str, position: Optional[int] = None):
        """
        Add track to playback queue

        Args:
            recording_mbid: MusicBrainz recording ID
            position: Position in queue (None = end of queue)
        """
        if position is None:
            self.queue.append(recording_mbid)
        else:
            self.queue.insert(position, recording_mbid)

        # Save to database if session exists
        if self.current_session_id:
            from listenbrainz.db import musicmatch as db_musicmatch

            try:
                db_musicmatch.add_to_playback_queue(
                    session_id=self.current_session_id,
                    recording_mbid=recording_mbid,
                    position=len(self.queue) - 1 if position is None else position
                )
            except Exception as e:
                current_app.logger.error(f"Error adding to queue: {e}")

    def get_queue(self) -> List[str]:
        """
        Get current playback queue

        Returns:
            List of recording MBIDs
        """
        return self.queue.copy()

    def clear_queue(self):
        """Clear the playback queue"""
        self.queue.clear()

    def get_next_track(self) -> Optional[str]:
        """
        Get next track from queue

        Returns:
            Recording MBID or None
        """
        if not self.queue:
            return None

        return self.queue.pop(0)

    def switch_service(self, new_service: str) -> bool:
        """
        Switch playback to a different service

        Args:
            new_service: Service to switch to

        Returns:
            True if successful, False otherwise
        """
        if new_service not in self.get_user_connected_services():
            current_app.logger.error(
                f"Cannot switch to {new_service}: not connected"
            )
            return False

        # End current session
        self.end_session()

        # Create new session with new service
        try:
            self.create_session(new_service)
            return True
        except Exception as e:
            current_app.logger.error(f"Error switching service: {e}")
            return False

    def get_playback_info(self) -> Dict:
        """
        Get current playback information

        Returns:
            Dict with playback state, current track, service, etc.
        """
        return {
            "session_id": self.current_session_id,
            "service": self.current_service,
            "state": self.current_state.value,
            "current_track": self.current_track,
            "queue_length": len(self.queue),
            "queue": self.queue,
        }

    def set_playback_state(self, state: PlaybackState, track_mbid: Optional[str] = None):
        """
        Update playback state

        Args:
            state: New playback state
            track_mbid: Currently playing track MBID
        """
        self.current_state = state

        if track_mbid:
            self.current_track = track_mbid

            # Mark track as played in queue
            if self.current_session_id:
                from listenbrainz.db import musicmatch as db_musicmatch

                try:
                    db_musicmatch.mark_track_played(
                        session_id=self.current_session_id,
                        recording_mbid=track_mbid
                    )
                except Exception as e:
                    current_app.logger.error(f"Error marking track played: {e}")
