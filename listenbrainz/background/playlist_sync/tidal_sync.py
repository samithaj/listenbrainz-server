"""
Tidal Playlist Sync

Handles playlist synchronization with Tidal
"""

from typing import Dict, List, Optional
import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.background.playlist_sync.base_sync import BasePlaylistSync
from listenbrainz.domain.tidal import TidalService


class TidalPlaylistSync(BasePlaylistSync):
    """Tidal-specific playlist synchronization"""

    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.base_url = "https://api.tidal.com/v1"

    def get_service_type(self):
        return ExternalServiceType.TIDAL

    def get_service_instance(self):
        return TidalService()

    def create_playlist(self, playlist_data: Dict) -> Dict:
        """Create a new playlist on Tidal"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create playlist
        payload = {
            "title": playlist_data.get("name", "Untitled Playlist"),
            "description": playlist_data.get("description", "Synced from ListenBrainz")
        }

        try:
            response = requests.post(
                f"{self.base_url}/playlists",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            playlist = response.json()
            playlist_id = playlist.get("uuid") or playlist.get("id")

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
            current_app.logger.error(f"Error creating Tidal playlist: {e}")
            raise

    def update_playlist(self, external_playlist_id: str, playlist_data: Dict) -> Dict:
        """Update an existing Tidal playlist"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Update playlist metadata
        metadata = {}
        if "name" in playlist_data:
            metadata["title"] = playlist_data["name"]
        if "description" in playlist_data:
            metadata["description"] = playlist_data["description"]

        if metadata:
            try:
                response = requests.put(
                    f"{self.base_url}/playlists/{external_playlist_id}",
                    headers=headers,
                    json=metadata
                )
                response.raise_for_status()
            except requests.RequestException as e:
                current_app.logger.error(f"Error updating Tidal playlist metadata: {e}")

        # Update tracks - replace all
        tracks = playlist_data.get("tracks", [])
        if tracks:
            self._clear_playlist_tracks(external_playlist_id, access_token)
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
        """Delete a Tidal playlist"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.delete(
                f"{self.base_url}/playlists/{external_playlist_id}",
                headers=headers
            )
            return response.status_code in [200, 204]
        except requests.RequestException as e:
            current_app.logger.error(f"Error deleting Tidal playlist: {e}")
            return False

    def get_playlist(self, external_playlist_id: str) -> Optional[Dict]:
        """Get playlist data from Tidal"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(
                f"{self.base_url}/playlists/{external_playlist_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            current_app.logger.error(f"Error fetching Tidal playlist: {e}")
            return None

    def search_track(self, track_name: str, artist_name: str) -> Optional[str]:
        """Search for a track on Tidal"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        query = f"{track_name} {artist_name}"
        params = {
            "query": query,
            "type": "TRACKS",
            "limit": 1
        }

        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            results = response.json()
            if results.get("tracks", {}).get("items"):
                return str(results["tracks"]["items"][0]["id"])

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error searching Tidal: {e}")
            return None

    def _add_tracks_to_playlist(
        self,
        playlist_id: str,
        tracks: List[Dict],
        access_token: str
    ) -> tuple:
        """Add tracks to a Tidal playlist"""
        headers = {"Authorization": f"Bearer {access_token}"}

        # Resolve tracks to Tidal IDs
        resolved_tracks = self.resolve_tracks(tracks, "tidal")

        track_ids = [t["external_track_id"] for t in resolved_tracks]

        if not track_ids:
            return 0, len(tracks)

        # Add tracks - Tidal may have different batch limits
        try:
            response = requests.post(
                f"{self.base_url}/playlists/{playlist_id}/tracks",
                headers=headers,
                json={"trackIds": track_ids}
            )
            response.raise_for_status()

            tracks_synced = len(track_ids)
            tracks_failed = len(tracks) - tracks_synced

            return tracks_synced, tracks_failed

        except requests.RequestException as e:
            current_app.logger.error(f"Error adding tracks to Tidal playlist: {e}")
            return 0, len(tracks)

    def _clear_playlist_tracks(self, playlist_id: str, access_token: str):
        """Remove all tracks from a Tidal playlist"""
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            # Get current tracks
            response = requests.get(
                f"{self.base_url}/playlists/{playlist_id}/tracks",
                headers=headers
            )
            response.raise_for_status()

            tracks = response.json().get("items", [])
            track_ids = [str(track["id"]) for track in tracks]

            if track_ids:
                # Remove tracks
                requests.delete(
                    f"{self.base_url}/playlists/{playlist_id}/tracks",
                    headers=headers,
                    json={"trackIds": track_ids}
                )

        except requests.RequestException as e:
            current_app.logger.error(f"Error clearing Tidal playlist: {e}")
