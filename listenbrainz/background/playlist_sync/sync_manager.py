"""
Playlist Sync Manager

Orchestrates playlist synchronization across multiple music services.
Manages sync jobs, tracks status, and handles conflicts.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Set
from enum import Enum
import sqlalchemy
from flask import current_app

from data.model.external_service import ExternalServiceType
from listenbrainz.webserver import db_conn


class SyncStatus(Enum):
    """Sync status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some services succeeded, some failed


class PlaylistSyncManager:
    """Manages playlist synchronization across multiple services"""

    def __init__(self, user_id: int, playlist_id: str):
        self.user_id = user_id
        self.playlist_id = playlist_id
        self.sync_results = {}

    def sync_to_services(
        self,
        services: List[str],
        playlist_data: Dict,
        force: bool = False
    ) -> Dict:
        """
        Sync a playlist to specified services

        Args:
            services: List of service names to sync to
            playlist_data: Playlist data including tracks
            force: Force sync even if already synced

        Returns:
            Dict with sync results per service
        """
        results = {
            "playlist_id": self.playlist_id,
            "services": {},
            "overall_status": SyncStatus.PENDING.value,
            "synced_at": datetime.now().isoformat()
        }

        # Get sync settings
        settings = self._get_sync_settings()
        enabled_services = set(settings.get("sync_services", []))

        # Filter services based on settings unless forced
        if not force:
            services = [s for s in services if s in enabled_services]

        if not services:
            results["overall_status"] = SyncStatus.COMPLETED.value
            results["message"] = "No services enabled for sync"
            return results

        # Update status to in progress
        self._update_overall_status(SyncStatus.IN_PROGRESS)

        success_count = 0
        failure_count = 0

        # Sync to each service
        for service in services:
            try:
                service_result = self._sync_to_service(service, playlist_data)
                results["services"][service] = service_result

                if service_result["status"] == "completed":
                    success_count += 1
                else:
                    failure_count += 1

            except Exception as e:
                current_app.logger.error(
                    f"Error syncing playlist {self.playlist_id} to {service}: {e}",
                    exc_info=True
                )
                results["services"][service] = {
                    "status": "failed",
                    "error": str(e)
                }
                failure_count += 1

        # Determine overall status
        if failure_count == 0:
            overall_status = SyncStatus.COMPLETED
        elif success_count == 0:
            overall_status = SyncStatus.FAILED
        else:
            overall_status = SyncStatus.PARTIAL

        results["overall_status"] = overall_status.value
        results["success_count"] = success_count
        results["failure_count"] = failure_count

        # Update database
        self._update_overall_status(overall_status)

        return results

    def _sync_to_service(self, service: str, playlist_data: Dict) -> Dict:
        """
        Sync playlist to a specific service

        Args:
            service: Service name
            playlist_data: Playlist data

        Returns:
            Dict with sync result
        """
        # Update status to in progress
        self._update_service_status(service, SyncStatus.IN_PROGRESS, None)

        try:
            # Get service-specific sync handler
            sync_handler = self._get_sync_handler(service)

            # Check if playlist already exists on service
            external_playlist_id = self._get_external_playlist_id(service)

            if external_playlist_id:
                # Update existing playlist
                result = sync_handler.update_playlist(
                    external_playlist_id,
                    playlist_data
                )
            else:
                # Create new playlist
                result = sync_handler.create_playlist(playlist_data)
                external_playlist_id = result["playlist_id"]

                # Save mapping
                self._save_playlist_mapping(service, external_playlist_id)

            # Update status to completed
            self._update_service_status(
                service,
                SyncStatus.COMPLETED,
                None
            )

            return {
                "status": "completed",
                "external_playlist_id": external_playlist_id,
                "tracks_synced": result.get("tracks_synced", 0),
                "tracks_failed": result.get("tracks_failed", 0)
            }

        except Exception as e:
            # Update status to failed
            self._update_service_status(
                service,
                SyncStatus.FAILED,
                str(e)
            )
            raise

    def _get_sync_handler(self, service: str):
        """Get service-specific sync handler"""
        from listenbrainz.background.playlist_sync import (
            spotify_sync,
            tidal_sync,
            youtube_music_sync,
            apple_music_sync
        )

        handlers = {
            ExternalServiceType.SPOTIFY.value: spotify_sync.SpotifyPlaylistSync(self.user_id),
            ExternalServiceType.TIDAL.value: tidal_sync.TidalPlaylistSync(self.user_id),
            ExternalServiceType.YOUTUBE_MUSIC.value: youtube_music_sync.YoutubeMusicPlaylistSync(self.user_id),
            ExternalServiceType.APPLE.value: apple_music_sync.AppleMusicPlaylistSync(self.user_id),
        }

        if service not in handlers:
            raise ValueError(f"Unsupported service: {service}")

        return handlers[service]

    def _get_sync_settings(self) -> Dict:
        """Get playlist sync settings"""
        query = """
            SELECT auto_sync_enabled,
                   sync_services,
                   sync_frequency_minutes
              FROM musicmatch.playlist_sync_settings
             WHERE lb_playlist_id = :playlist_id
        """

        try:
            result = db_conn.execute(
                sqlalchemy.text(query),
                {"playlist_id": self.playlist_id}
            ).fetchone()

            if result:
                return {
                    "auto_sync_enabled": result.auto_sync_enabled,
                    "sync_services": result.sync_services or [],
                    "sync_frequency_minutes": result.sync_frequency_minutes
                }

            return {
                "auto_sync_enabled": False,
                "sync_services": [],
                "sync_frequency_minutes": 60
            }

        except Exception as e:
            current_app.logger.error(f"Error fetching sync settings: {e}")
            return {}

    def _get_external_playlist_id(self, service: str) -> Optional[str]:
        """Get external playlist ID for a service"""
        query = """
            SELECT external_playlist_id
              FROM musicmatch.playlist_sync_mapping
             WHERE lb_playlist_id = :playlist_id
               AND service = :service
        """

        try:
            result = db_conn.execute(
                sqlalchemy.text(query),
                {
                    "playlist_id": self.playlist_id,
                    "service": service
                }
            ).fetchone()

            return result.external_playlist_id if result else None

        except Exception as e:
            current_app.logger.error(f"Error fetching external playlist ID: {e}")
            return None

    def _save_playlist_mapping(self, service: str, external_playlist_id: str):
        """Save playlist mapping to database"""
        query = """
            INSERT INTO musicmatch.playlist_sync_mapping
                (lb_playlist_id, service, external_playlist_id, last_synced, sync_status)
            VALUES
                (:playlist_id, :service, :external_playlist_id, NOW(), :status)
            ON CONFLICT (lb_playlist_id, service)
            DO UPDATE SET
                external_playlist_id = EXCLUDED.external_playlist_id,
                last_synced = NOW(),
                sync_status = EXCLUDED.sync_status
        """

        try:
            db_conn.execute(
                sqlalchemy.text(query),
                {
                    "playlist_id": self.playlist_id,
                    "service": service,
                    "external_playlist_id": external_playlist_id,
                    "status": SyncStatus.COMPLETED.value
                }
            )
            db_conn.commit()

        except Exception as e:
            current_app.logger.error(f"Error saving playlist mapping: {e}")
            db_conn.rollback()
            raise

    def _update_service_status(
        self,
        service: str,
        status: SyncStatus,
        error_message: Optional[str]
    ):
        """Update sync status for a service"""
        query = """
            UPDATE musicmatch.playlist_sync_mapping
               SET sync_status = :status,
                   error_message = :error_message,
                   last_synced = CASE WHEN :status = 'completed' THEN NOW() ELSE last_synced END
             WHERE lb_playlist_id = :playlist_id
               AND service = :service
        """

        try:
            db_conn.execute(
                sqlalchemy.text(query),
                {
                    "status": status.value,
                    "error_message": error_message,
                    "playlist_id": self.playlist_id,
                    "service": service
                }
            )
            db_conn.commit()

        except Exception as e:
            current_app.logger.error(f"Error updating service status: {e}")
            db_conn.rollback()

    def _update_overall_status(self, status: SyncStatus):
        """Update overall sync status"""
        # This could be stored in a separate table or logged
        current_app.logger.info(
            f"Playlist {self.playlist_id} sync status: {status.value}"
        )

    def get_sync_status(self) -> Dict:
        """Get current sync status for all services"""
        query = """
            SELECT service,
                   external_playlist_id,
                   last_synced,
                   sync_status,
                   error_message
              FROM musicmatch.playlist_sync_mapping
             WHERE lb_playlist_id = :playlist_id
        """

        try:
            result = db_conn.execute(
                sqlalchemy.text(query),
                {"playlist_id": self.playlist_id}
            )

            services = {}
            for row in result:
                services[row.service] = {
                    "external_playlist_id": row.external_playlist_id,
                    "last_synced": row.last_synced.isoformat() if row.last_synced else None,
                    "status": row.sync_status,
                    "error": row.error_message
                }

            return {
                "playlist_id": self.playlist_id,
                "services": services
            }

        except Exception as e:
            current_app.logger.error(f"Error fetching sync status: {e}")
            return {
                "playlist_id": self.playlist_id,
                "services": {},
                "error": str(e)
            }


def get_playlists_needing_sync() -> List[Dict]:
    """
    Get playlists that need automatic synchronization

    Returns:
        List of playlist info dicts
    """
    query = """
        SELECT DISTINCT pss.lb_playlist_id,
               pss.sync_services,
               pss.sync_frequency_minutes,
               psm.last_synced
          FROM musicmatch.playlist_sync_settings pss
     LEFT JOIN musicmatch.playlist_sync_mapping psm
            ON pss.lb_playlist_id = psm.lb_playlist_id
         WHERE pss.auto_sync_enabled = true
           AND (psm.last_synced IS NULL
            OR psm.last_synced < NOW() - (pss.sync_frequency_minutes || ' minutes')::INTERVAL)
    """

    try:
        result = db_conn.execute(sqlalchemy.text(query))
        return [
            {
                "playlist_id": row.lb_playlist_id,
                "services": row.sync_services,
                "frequency_minutes": row.sync_frequency_minutes,
                "last_synced": row.last_synced.isoformat() if row.last_synced else None
            }
            for row in result
        ]

    except Exception as e:
        current_app.logger.error(f"Error fetching playlists needing sync: {e}")
        return []
