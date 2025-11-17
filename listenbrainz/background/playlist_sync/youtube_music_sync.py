"""
YouTube Music Playlist Sync

Handles playlist synchronization with YouTube Music
"""

from typing import Dict, List, Optional
import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.background.playlist_sync.base_sync import BasePlaylistSync
from listenbrainz.domain.youtube_music import YoutubeMusicService


class YoutubeMusicPlaylistSync(BasePlaylistSync):
    """YouTube Music-specific playlist synchronization"""

    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def get_service_type(self):
        return ExternalServiceType.YOUTUBE_MUSIC

    def get_service_instance(self):
        return YoutubeMusicService()

    def create_playlist(self, playlist_data: Dict) -> Dict:
        """Create a new playlist on YouTube Music"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create playlist using YouTube Data API
        payload = {
            "snippet": {
                "title": playlist_data.get("name", "Untitled Playlist"),
                "description": playlist_data.get("description", "Synced from ListenBrainz")
            },
            "status": {
                "privacyStatus": "private" if not playlist_data.get("public", False) else "public"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/playlists",
                headers=headers,
                params={"part": "snippet,status"},
                json=payload
            )
            response.raise_for_status()

            playlist = response.json()
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
            current_app.logger.error(f"Error creating YouTube Music playlist: {e}")
            raise

    def update_playlist(self, external_playlist_id: str, playlist_data: Dict) -> Dict:
        """Update an existing YouTube Music playlist"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Update playlist metadata
        update_payload = {
            "id": external_playlist_id,
            "snippet": {},
            "status": {}
        }

        if "name" in playlist_data:
            update_payload["snippet"]["title"] = playlist_data["name"]
        if "description" in playlist_data:
            update_payload["snippet"]["description"] = playlist_data["description"]
        if "public" in playlist_data:
            update_payload["status"]["privacyStatus"] = "public" if playlist_data["public"] else "private"

        if update_payload["snippet"] or update_payload["status"]:
            try:
                response = requests.put(
                    f"{self.base_url}/playlists",
                    headers=headers,
                    params={"part": "snippet,status"},
                    json=update_payload
                )
                response.raise_for_status()
            except requests.RequestException as e:
                current_app.logger.error(f"Error updating YouTube Music playlist: {e}")

        # Update tracks
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
        """Delete a YouTube Music playlist"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.delete(
                f"{self.base_url}/playlists",
                headers=headers,
                params={"id": external_playlist_id}
            )
            return response.status_code in [200, 204]
        except requests.RequestException as e:
            current_app.logger.error(f"Error deleting YouTube Music playlist: {e}")
            return False

    def get_playlist(self, external_playlist_id: str) -> Optional[Dict]:
        """Get playlist data from YouTube Music"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(
                f"{self.base_url}/playlists",
                headers=headers,
                params={
                    "part": "snippet,status",
                    "id": external_playlist_id
                }
            )
            response.raise_for_status()

            playlists = response.json().get("items", [])
            return playlists[0] if playlists else None

        except requests.RequestException as e:
            current_app.logger.error(f"Error fetching YouTube Music playlist: {e}")
            return None

    def search_track(self, track_name: str, artist_name: str) -> Optional[str]:
        """Search for a track on YouTube Music"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        query = f"{track_name} {artist_name}"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "videoCategoryId": "10",  # Music category
            "maxResults": 1
        }

        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            results = response.json()
            if results.get("items"):
                return results["items"][0]["id"]["videoId"]

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error searching YouTube Music: {e}")
            return None

    def _add_tracks_to_playlist(
        self,
        playlist_id: str,
        tracks: List[Dict],
        access_token: str
    ) -> tuple:
        """Add tracks to a YouTube Music playlist"""
        headers = {"Authorization": f"Bearer {access_token}"}

        # Resolve tracks to YouTube video IDs
        resolved_tracks = self.resolve_tracks(tracks, "youtube_music")

        if not resolved_tracks:
            return 0, len(tracks)

        tracks_synced = 0

        # Add tracks one by one (YouTube API adds one at a time)
        for track in resolved_tracks:
            try:
                payload = {
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": track["external_track_id"]
                        }
                    }
                }

                response = requests.post(
                    f"{self.base_url}/playlistItems",
                    headers=headers,
                    params={"part": "snippet"},
                    json=payload
                )
                response.raise_for_status()
                tracks_synced += 1

            except requests.RequestException as e:
                current_app.logger.error(
                    f"Error adding track to YouTube Music playlist: {e}"
                )

        tracks_failed = len(tracks) - tracks_synced

        return tracks_synced, tracks_failed

    def _clear_playlist_tracks(self, playlist_id: str, access_token: str):
        """Remove all tracks from a YouTube Music playlist"""
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            # Get current tracks
            response = requests.get(
                f"{self.base_url}/playlistItems",
                headers=headers,
                params={
                    "part": "id",
                    "playlistId": playlist_id,
                    "maxResults": 50
                }
            )
            response.raise_for_status()

            items = response.json().get("items", [])

            # Delete each item
            for item in items:
                try:
                    requests.delete(
                        f"{self.base_url}/playlistItems",
                        headers=headers,
                        params={"id": item["id"]}
                    )
                except requests.RequestException:
                    pass  # Continue with other items

        except requests.RequestException as e:
            current_app.logger.error(f"Error clearing YouTube Music playlist: {e}")
