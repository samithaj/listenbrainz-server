"""
Apple Music Playlist Sync

Handles playlist synchronization with Apple Music
"""

from typing import Dict, List, Optional
import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.background.playlist_sync.base_sync import BasePlaylistSync
from listenbrainz.domain.apple import AppleService


class AppleMusicPlaylistSync(BasePlaylistSync):
    """Apple Music-specific playlist synchronization"""

    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.base_url = "https://api.music.apple.com/v1"

    def get_service_type(self):
        return ExternalServiceType.APPLE

    def get_service_instance(self):
        return AppleService()

    def create_playlist(self, playlist_data: Dict) -> Dict:
        """Create a new playlist on Apple Music"""
        access_token = self.get_user_token()  # This is the music user token
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create playlist using Apple Music API
        payload = {
            "attributes": {
                "name": playlist_data.get("name", "Untitled Playlist"),
                "description": playlist_data.get("description", "Synced from ListenBrainz")
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/me/library/playlists",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            playlist = response.json()["data"][0]
            playlist_id = playlist["id"]

            # Add tracks if provided
            tracks = playlist_data.get("tracks", [])
            tracks_synced, tracks_failed = self._add_tracks_to_playlist(
                playlist_id,
                tracks,
                access_token
            )

            return {
                "playlist_id": playlist_id,
                "tracks_synced": tracks_synced,
                "tracks_failed": tracks_failed
            }

        except requests.RequestException as e:
            current_app.logger.error(f"Error creating Apple Music playlist: {e}")
            raise

    def update_playlist(self, external_playlist_id: str, playlist_data: Dict) -> Dict:
        """Update an existing Apple Music playlist"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Update playlist metadata
        attributes = {}
        if "name" in playlist_data:
            attributes["name"] = playlist_data["name"]
        if "description" in playlist_data:
            attributes["description"] = playlist_data["description"]

        if attributes:
            try:
                payload = {"attributes": attributes}
                response = requests.patch(
                    f"{self.base_url}/me/library/playlists/{external_playlist_id}",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
            except requests.RequestException as e:
                current_app.logger.error(f"Error updating Apple Music playlist: {e}")

        # Update tracks - replace all
        tracks = playlist_data.get("tracks", [])
        if tracks:
            # Apple Music doesn't have a clear endpoint, need to get existing tracks and remove them
            # For simplicity, we'll just add new tracks
            tracks_synced, tracks_failed = self._add_tracks_to_playlist(
                external_playlist_id,
                tracks,
                access_token
            )
        else:
            tracks_synced = 0
            tracks_failed = 0

        return {
            "tracks_synced": tracks_synced,
            "tracks_failed": tracks_failed
        }

    def delete_playlist(self, external_playlist_id: str) -> bool:
        """Delete an Apple Music playlist"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.delete(
                f"{self.base_url}/me/library/playlists/{external_playlist_id}",
                headers=headers
            )
            return response.status_code in [200, 204]
        except requests.RequestException as e:
            current_app.logger.error(f"Error deleting Apple Music playlist: {e}")
            return False

    def get_playlist(self, external_playlist_id: str) -> Optional[Dict]:
        """Get playlist data from Apple Music"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(
                f"{self.base_url}/me/library/playlists/{external_playlist_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()["data"][0]
        except requests.RequestException as e:
            current_app.logger.error(f"Error fetching Apple Music playlist: {e}")
            return None

    def search_track(self, track_name: str, artist_name: str) -> Optional[str]:
        """Search for a track on Apple Music"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        query = f"{track_name} {artist_name}"
        params = {
            "term": query,
            "types": "songs",
            "limit": 1
        }

        try:
            response = requests.get(
                f"{self.base_url}/catalog/us/search",  # TODO: Use user's storefront
                headers=headers,
                params=params
            )
            response.raise_for_status()

            results = response.json()
            if results.get("results", {}).get("songs", {}).get("data"):
                return results["results"]["songs"]["data"][0]["id"]

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error searching Apple Music: {e}")
            return None

    def _add_tracks_to_playlist(
        self,
        playlist_id: str,
        tracks: List[Dict],
        access_token: str
    ) -> tuple:
        """Add tracks to an Apple Music playlist"""
        headers = {"Authorization": f"Bearer {access_token}"}

        # Resolve tracks to Apple Music IDs
        resolved_tracks = self.resolve_tracks(tracks, "apple")

        track_items = [
            {"id": t["external_track_id"], "type": "songs"}
            for t in resolved_tracks
        ]

        if not track_items:
            return 0, len(tracks)

        try:
            payload = {"data": track_items}

            response = requests.post(
                f"{self.base_url}/me/library/playlists/{playlist_id}/tracks",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            tracks_synced = len(track_items)
            tracks_failed = len(tracks) - tracks_synced

            return tracks_synced, tracks_failed

        except requests.RequestException as e:
            current_app.logger.error(f"Error adding tracks to Apple Music playlist: {e}")
            return 0, len(tracks)
