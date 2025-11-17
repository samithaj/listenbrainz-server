"""
Spotify Playlist Sync

Handles playlist synchronization with Spotify
"""

from typing import Dict, List, Optional
import requests
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.background.playlist_sync.base_sync import BasePlaylistSync
from listenbrainz.domain.spotify import SpotifyService


class SpotifyPlaylistSync(BasePlaylistSync):
    """Spotify-specific playlist synchronization"""

    def __init__(self, user_id: int):
        super().__init__(user_id)
        self.base_url = "https://api.spotify.com/v1"

    def get_service_type(self):
        return ExternalServiceType.SPOTIFY

    def get_service_instance(self):
        return SpotifyService()

    def create_playlist(self, playlist_data: Dict) -> Dict:
        """Create a new playlist on Spotify"""
        access_token = self.get_user_token()

        # Get Spotify user ID first
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(f"{self.base_url}/me", headers=headers)
        user_response.raise_for_status()
        spotify_user_id = user_response.json()["id"]

        # Create playlist
        playlist_payload = {
            "name": playlist_data.get("name", "Untitled Playlist"),
            "description": playlist_data.get("description", "Synced from ListenBrainz"),
            "public": playlist_data.get("public", False)
        }

        response = requests.post(
            f"{self.base_url}/users/{spotify_user_id}/playlists",
            headers=headers,
            json=playlist_payload
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

    def update_playlist(self, external_playlist_id: str, playlist_data: Dict) -> Dict:
        """Update an existing Spotify playlist"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Update playlist metadata
        metadata = {}
        if "name" in playlist_data:
            metadata["name"] = playlist_data["name"]
        if "description" in playlist_data:
            metadata["description"] = playlist_data["description"]
        if "public" in playlist_data:
            metadata["public"] = playlist_data["public"]

        if metadata:
            response = requests.put(
                f"{self.base_url}/playlists/{external_playlist_id}",
                headers=headers,
                json=metadata
            )
            response.raise_for_status()

        # Update tracks - replace all tracks
        tracks = playlist_data.get("tracks", [])
        if tracks:
            # First, clear existing tracks
            self._clear_playlist_tracks(external_playlist_id, access_token)

            # Then add new tracks
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
        """Delete (unfollow) a Spotify playlist"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Spotify doesn't have a delete endpoint, use unfollow
        response = requests.delete(
            f"{self.base_url}/playlists/{external_playlist_id}/followers",
            headers=headers
        )

        return response.status_code == 200

    def get_playlist(self, external_playlist_id: str) -> Optional[Dict]:
        """Get playlist data from Spotify"""
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
            current_app.logger.error(f"Error fetching Spotify playlist: {e}")
            return None

    def search_track(self, track_name: str, artist_name: str) -> Optional[str]:
        """Search for a track on Spotify"""
        access_token = self.get_user_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        query = f"track:{track_name} artist:{artist_name}"
        params = {
            "q": query,
            "type": "track",
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
            if results["tracks"]["items"]:
                return results["tracks"]["items"][0]["id"]

            return None

        except requests.RequestException as e:
            current_app.logger.error(f"Error searching Spotify: {e}")
            return None

    def _add_tracks_to_playlist(
        self,
        playlist_id: str,
        tracks: List[Dict],
        access_token: str
    ) -> tuple:
        """Add tracks to a Spotify playlist"""
        headers = {"Authorization": f"Bearer {access_token}"}

        # Resolve tracks to Spotify IDs
        resolved_tracks = self.resolve_tracks(tracks, "spotify")

        track_uris = [
            f"spotify:track:{t['external_track_id']}"
            for t in resolved_tracks
        ]

        if not track_uris:
            return 0, len(tracks)

        # Spotify allows max 100 tracks per request
        batch_size = 100
        tracks_synced = 0

        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]

            try:
                response = requests.post(
                    f"{self.base_url}/playlists/{playlist_id}/tracks",
                    headers=headers,
                    json={"uris": batch}
                )
                response.raise_for_status()
                tracks_synced += len(batch)

            except requests.RequestException as e:
                current_app.logger.error(
                    f"Error adding tracks to Spotify playlist: {e}"
                )
                break

        tracks_failed = len(tracks) - tracks_synced

        return tracks_synced, tracks_failed

    def _clear_playlist_tracks(self, playlist_id: str, access_token: str):
        """Remove all tracks from a Spotify playlist"""
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get current tracks
        try:
            response = requests.get(
                f"{self.base_url}/playlists/{playlist_id}/tracks",
                headers=headers,
                params={"fields": "items(track(uri))"}
            )
            response.raise_for_status()

            tracks = response.json()["items"]
            track_uris = [item["track"]["uri"] for item in tracks if item.get("track")]

            if track_uris:
                # Remove in batches of 100
                batch_size = 100
                for i in range(0, len(track_uris), batch_size):
                    batch = track_uris[i:i + batch_size]
                    requests.delete(
                        f"{self.base_url}/playlists/{playlist_id}/tracks",
                        headers=headers,
                        json={"tracks": [{"uri": uri} for uri in batch]}
                    )

        except requests.RequestException as e:
            current_app.logger.error(
                f"Error clearing Spotify playlist: {e}"
            )
