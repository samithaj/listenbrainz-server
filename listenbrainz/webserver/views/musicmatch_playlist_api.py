"""
MusicMatch Playlist API Blueprint

Provides endpoints for unified playlist management and synchronization
"""

import uuid
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
import sqlalchemy
from typing import Optional

from listenbrainz.background.playlist_sync import PlaylistSyncManager
from listenbrainz.webserver import db_conn
from listenbrainz.webserver.decorators import crossdomain
from listenbrainz.webserver.errors import (
    APIBadRequest,
    APINotFound,
    APIInternalServerError,
    APIUnauthorized
)
from listenbrainz.webserver.rate_limiter import ratelimit
from data.model.external_service import ExternalServiceType

musicmatch_playlist_api_bp = Blueprint('musicmatch_playlist_api', __name__)


@musicmatch_playlist_api_bp.route('/<playlist_id>/sync', methods=['POST', 'OPTIONS'])
@crossdomain()
@ratelimit()
@login_required
def sync_playlist(playlist_id: str):
    """
    Trigger synchronization of a playlist to external services

    Request body:
    {
        "services": ["spotify", "tidal", "youtube_music"],
        "force": false
    }

    Response:
    {
        "job_id": "uuid",
        "playlist_id": "uuid",
        "services": {
            "spotify": {
                "status": "completed",
                "external_playlist_id": "...",
                "tracks_synced": 20,
                "tracks_failed": 0
            },
            ...
        },
        "overall_status": "completed",
        "success_count": 2,
        "failure_count": 0
    }

    :param playlist_id: ListenBrainz playlist UUID
    :statuscode 200: Sync completed
    :statuscode 202: Sync started (async)
    :statuscode 400: Bad request
    :statuscode 401: Unauthorized
    :statuscode 404: Playlist not found
    :statuscode 500: Internal server error
    """
    try:
        # Validate playlist UUID
        try:
            uuid.UUID(playlist_id)
        except ValueError:
            raise APIBadRequest(f"Invalid playlist ID format: {playlist_id}")

        # Parse request body
        data = request.json or {}
        services = data.get('services', [])
        force = data.get('force', False)

        if not services:
            raise APIBadRequest("At least one service must be specified")

        # Validate services
        valid_services = {s.value for s in ExternalServiceType}
        for service in services:
            if service not in valid_services:
                raise APIBadRequest(f"Invalid service: {service}")

        # TODO: Verify user owns the playlist
        # For now, we'll assume they do

        # Get playlist data
        playlist_data = _get_playlist_data(playlist_id)
        if not playlist_data:
            raise APINotFound(f"Playlist {playlist_id} not found")

        # Create sync job
        job_id = _create_sync_job(playlist_id, services)

        # Perform sync
        sync_manager = PlaylistSyncManager(current_user.id, playlist_id)
        results = sync_manager.sync_to_services(services, playlist_data, force=force)

        # Update job status
        _update_sync_job(
            job_id,
            results["overall_status"],
            results.get("success_count", 0),
            results.get("failure_count", 0)
        )

        results["job_id"] = job_id

        return jsonify(results)

    except APIBadRequest:
        raise
    except APINotFound:
        raise
    except Exception as e:
        current_app.logger.error(f"Error syncing playlist {playlist_id}: {e}", exc_info=True)
        raise APIInternalServerError("Failed to sync playlist")


@musicmatch_playlist_api_bp.route('/<playlist_id>/sync-status', methods=['GET', 'OPTIONS'])
@crossdomain()
@ratelimit()
def get_sync_status(playlist_id: str):
    """
    Get current sync status for a playlist

    Response:
    {
        "playlist_id": "uuid",
        "services": {
            "spotify": {
                "external_playlist_id": "...",
                "last_synced": "2025-11-17T...",
                "status": "completed",
                "error": null
            },
            ...
        }
    }

    :param playlist_id: ListenBrainz playlist UUID
    :statuscode 200: Success
    :statuscode 400: Invalid playlist ID
    :statuscode 404: Playlist not found
    :statuscode 500: Internal server error
    """
    try:
        # Validate playlist UUID
        try:
            uuid.UUID(playlist_id)
        except ValueError:
            raise APIBadRequest(f"Invalid playlist ID format: {playlist_id}")

        # Get sync status
        sync_manager = PlaylistSyncManager(0, playlist_id)  # User ID not needed for status
        status = sync_manager.get_sync_status()

        return jsonify(status)

    except APIBadRequest:
        raise
    except Exception as e:
        current_app.logger.error(f"Error fetching sync status: {e}", exc_info=True)
        raise APIInternalServerError("Failed to fetch sync status")


@musicmatch_playlist_api_bp.route('/<playlist_id>/sync-settings', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain()
@ratelimit()
@login_required
def playlist_sync_settings(playlist_id: str):
    """
    Get or update playlist sync settings

    GET Response:
    {
        "auto_sync_enabled": true,
        "sync_services": ["spotify", "tidal"],
        "sync_frequency_minutes": 60
    }

    POST Request body:
    {
        "auto_sync_enabled": true,
        "sync_services": ["spotify", "tidal", "youtube_music"],
        "sync_frequency_minutes": 30
    }

    :param playlist_id: ListenBrainz playlist UUID
    :statuscode 200: Success
    :statuscode 400: Bad request
    :statuscode 401: Unauthorized
    :statuscode 500: Internal server error
    """
    try:
        # Validate playlist UUID
        try:
            uuid.UUID(playlist_id)
        except ValueError:
            raise APIBadRequest(f"Invalid playlist ID format: {playlist_id}")

        if request.method == 'GET':
            # Get current settings
            settings = _get_sync_settings(playlist_id)
            return jsonify(settings)

        else:  # POST
            data = request.json or {}

            auto_sync_enabled = data.get('auto_sync_enabled', True)
            sync_services = data.get('sync_services', [])
            sync_frequency_minutes = data.get('sync_frequency_minutes', 60)

            # Validate
            if not isinstance(auto_sync_enabled, bool):
                raise APIBadRequest("auto_sync_enabled must be boolean")

            if not isinstance(sync_services, list):
                raise APIBadRequest("sync_services must be an array")

            if not isinstance(sync_frequency_minutes, int) or sync_frequency_minutes < 1:
                raise APIBadRequest("sync_frequency_minutes must be a positive integer")

            # Validate services
            valid_services = {s.value for s in ExternalServiceType}
            for service in sync_services:
                if service not in valid_services:
                    raise APIBadRequest(f"Invalid service: {service}")

            # Save settings
            _save_sync_settings(
                playlist_id,
                auto_sync_enabled,
                sync_services,
                sync_frequency_minutes
            )

            return jsonify({
                "success": True,
                "message": "Sync settings updated successfully"
            })

    except APIBadRequest:
        raise
    except Exception as e:
        current_app.logger.error(f"Error managing sync settings: {e}", exc_info=True)
        raise APIInternalServerError("Failed to manage sync settings")


@musicmatch_playlist_api_bp.route('/jobs/<job_id>', methods=['GET', 'OPTIONS'])
@crossdomain()
@ratelimit()
def get_sync_job(job_id: str):
    """
    Get sync job status

    Response:
    {
        "job_id": "uuid",
        "playlist_id": "uuid",
        "services": ["spotify", "tidal"],
        "status": "completed",
        "started_at": "2025-11-17T...",
        "completed_at": "2025-11-17T...",
        "success_count": 2,
        "failure_count": 0
    }

    :param job_id: Sync job UUID
    :statuscode 200: Success
    :statuscode 400: Invalid job ID
    :statuscode 404: Job not found
    :statuscode 500: Internal server error
    """
    try:
        # Validate job UUID
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise APIBadRequest(f"Invalid job ID format: {job_id}")

        # Get job info
        query = """
            SELECT job_id,
                   lb_playlist_id,
                   services,
                   status,
                   started_at,
                   completed_at,
                   success_count,
                   failure_count,
                   error_message
              FROM musicmatch.playlist_sync_jobs
             WHERE job_id = :job_id
        """

        result = db_conn.execute(
            sqlalchemy.text(query),
            {"job_id": job_id}
        ).fetchone()

        if not result:
            raise APINotFound(f"Job {job_id} not found")

        return jsonify({
            "job_id": str(result.job_id),
            "playlist_id": str(result.lb_playlist_id),
            "services": result.services,
            "status": result.status,
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "error": result.error_message
        })

    except APIBadRequest:
        raise
    except APINotFound:
        raise
    except Exception as e:
        current_app.logger.error(f"Error fetching sync job: {e}", exc_info=True)
        raise APIInternalServerError("Failed to fetch sync job")


# Helper functions

def _get_playlist_data(playlist_id: str) -> Optional[dict]:
    """Get playlist data from ListenBrainz database"""
    # TODO: Integrate with actual playlist table
    # For now, return sample data
    query = """
        SELECT MBID as id,
               name,
               description,
               public
          FROM playlist.playlist
         WHERE MBID = :playlist_id
    """

    try:
        result = db_conn.execute(
            sqlalchemy.text(query),
            {"playlist_id": playlist_id}
        ).fetchone()

        if not result:
            return None

        # Get tracks
        tracks_query = """
            SELECT recording_mbid,
                   added_by,
                   added_at
              FROM playlist.playlist_recording
             WHERE playlist_id = (
                SELECT id FROM playlist.playlist WHERE MBID = :playlist_id
             )
          ORDER BY position
        """

        tracks_result = db_conn.execute(
            sqlalchemy.text(tracks_query),
            {"playlist_id": playlist_id}
        )

        tracks = [
            {
                "recording_mbid": str(row.recording_mbid),
                # Additional track metadata would be fetched here
            }
            for row in tracks_result
        ]

        return {
            "id": str(result.id),
            "name": result.name,
            "description": result.description,
            "public": result.public,
            "tracks": tracks
        }

    except Exception as e:
        current_app.logger.error(f"Error fetching playlist data: {e}")
        return None


def _create_sync_job(playlist_id: str, services: list) -> str:
    """Create a new sync job"""
    query = """
        INSERT INTO musicmatch.playlist_sync_jobs
            (lb_playlist_id, services, status, started_at)
        VALUES
            (:playlist_id, :services, 'running', NOW())
        RETURNING job_id
    """

    try:
        result = db_conn.execute(
            sqlalchemy.text(query),
            {
                "playlist_id": playlist_id,
                "services": services
            }
        ).fetchone()

        db_conn.commit()
        return str(result.job_id)

    except Exception as e:
        current_app.logger.error(f"Error creating sync job: {e}")
        db_conn.rollback()
        raise


def _update_sync_job(job_id: str, status: str, success_count: int, failure_count: int):
    """Update sync job status"""
    query = """
        UPDATE musicmatch.playlist_sync_jobs
           SET status = :status,
               completed_at = NOW(),
               success_count = :success_count,
               failure_count = :failure_count
         WHERE job_id = :job_id
    """

    try:
        db_conn.execute(
            sqlalchemy.text(query),
            {
                "job_id": job_id,
                "status": status,
                "success_count": success_count,
                "failure_count": failure_count
            }
        )
        db_conn.commit()

    except Exception as e:
        current_app.logger.error(f"Error updating sync job: {e}")
        db_conn.rollback()


def _get_sync_settings(playlist_id: str) -> dict:
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
            {"playlist_id": playlist_id}
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


def _save_sync_settings(
    playlist_id: str,
    auto_sync_enabled: bool,
    sync_services: list,
    sync_frequency_minutes: int
):
    """Save playlist sync settings"""
    query = """
        INSERT INTO musicmatch.playlist_sync_settings
            (lb_playlist_id, auto_sync_enabled, sync_services, sync_frequency_minutes, updated_at)
        VALUES
            (:playlist_id, :auto_sync, :services, :frequency, NOW())
        ON CONFLICT (lb_playlist_id)
        DO UPDATE SET
            auto_sync_enabled = EXCLUDED.auto_sync_enabled,
            sync_services = EXCLUDED.sync_services,
            sync_frequency_minutes = EXCLUDED.sync_frequency_minutes,
            updated_at = NOW()
    """

    try:
        db_conn.execute(
            sqlalchemy.text(query),
            {
                "playlist_id": playlist_id,
                "auto_sync": auto_sync_enabled,
                "services": sync_services,
                "frequency": sync_frequency_minutes
            }
        )
        db_conn.commit()

    except Exception as e:
        current_app.logger.error(f"Error saving sync settings: {e}")
        db_conn.rollback()
        raise
