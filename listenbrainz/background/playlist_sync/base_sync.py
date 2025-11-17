"""
Base Playlist Sync Class

Provides common interface for service-specific playlist synchronization
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from flask import current_app


class BasePlaylistSync(ABC):
    """Base class for service-specific playlist sync implementations"""

    def __init__(self, user_id: int):
        self.user_id = user_id

    @abstractmethod
    def create_playlist(self, playlist_data: Dict) -> Dict:
        """
        Create a new playlist on the external service

        Args:
            playlist_data: Playlist info including name, description, tracks

        Returns:
            Dict with playlist_id and sync stats
        """
        pass

    @abstractmethod
    def update_playlist(self, external_playlist_id: str, playlist_data: Dict) -> Dict:
        """
        Update an existing playlist on the external service

        Args:
            external_playlist_id: External service's playlist ID
            playlist_data: Updated playlist data

        Returns:
            Dict with sync stats
        """
        pass

    @abstractmethod
    def delete_playlist(self, external_playlist_id: str) -> bool:
        """
        Delete a playlist from the external service

        Args:
            external_playlist_id: External service's playlist ID

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_playlist(self, external_playlist_id: str) -> Optional[Dict]:
        """
        Get playlist data from the external service

        Args:
            external_playlist_id: External service's playlist ID

        Returns:
            Playlist data or None if not found
        """
        pass

    def resolve_tracks(self, tracks: List[Dict], service_name: str) -> List[Dict]:
        """
        Resolve ListenBrainz tracks to external service track IDs

        Args:
            tracks: List of track dicts with recording_mbid or track metadata
            service_name: Target service name

        Returns:
            List of dicts with external_track_id and metadata
        """
        from listenbrainz.webserver import db_conn
        import sqlalchemy

        resolved_tracks = []

        for track in tracks:
            recording_mbid = track.get("recording_mbid")

            if recording_mbid:
                # Try to get from track_service_mapping
                query = """
                    SELECT external_track_id, confidence
                      FROM musicmatch.track_service_mapping
                     WHERE recording_mbid = :mbid
                       AND service = :service
                """

                try:
                    result = db_conn.execute(
                        sqlalchemy.text(query),
                        {
                            "mbid": recording_mbid,
                            "service": service_name
                        }
                    ).fetchone()

                    if result:
                        resolved_tracks.append({
                            "external_track_id": result.external_track_id,
                            "confidence": result.confidence,
                            "track_metadata": track
                        })
                        continue

                except Exception as e:
                    current_app.logger.warning(
                        f"Error resolving track {recording_mbid}: {e}"
                    )

            # If no MBID mapping, try fuzzy search using track metadata
            track_name = track.get("track_name")
            artist_name = track.get("artist_name")

            if track_name and artist_name:
                external_id = self.search_track(track_name, artist_name)
                if external_id:
                    resolved_tracks.append({
                        "external_track_id": external_id,
                        "confidence": 0.7,  # Lower confidence for fuzzy match
                        "track_metadata": track
                    })
                else:
                    # Track not found
                    current_app.logger.warning(
                        f"Could not resolve track: {track_name} by {artist_name}"
                    )

        return resolved_tracks

    @abstractmethod
    def search_track(self, track_name: str, artist_name: str) -> Optional[str]:
        """
        Search for a track on the external service

        Args:
            track_name: Track name
            artist_name: Artist name

        Returns:
            External track ID if found, None otherwise
        """
        pass

    def get_user_token(self):
        """Get user's access token for the service"""
        from listenbrainz.db import external_service_oauth
        from listenbrainz.webserver import db_conn

        # This should be implemented by subclasses to specify their service type
        service_type = self.get_service_type()
        user = external_service_oauth.get_token(db_conn, self.user_id, service_type)

        if not user:
            raise ValueError(f"User not authenticated with {service_type.value}")

        # Check if token needs refresh
        from listenbrainz.domain.external_service import ExternalService
        service = self.get_service_instance()

        if service.user_oauth_token_has_expired(user):
            user = service.refresh_access_token(self.user_id, user["refresh_token"])

        return user["access_token"]

    @abstractmethod
    def get_service_type(self):
        """Get the ExternalServiceType for this service"""
        pass

    @abstractmethod
    def get_service_instance(self):
        """Get the service instance (e.g., SpotifyService)"""
        pass
