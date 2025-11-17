"""
MusicMatch API Blueprint

Provides endpoints for:
- Cross-service track resolution
- Multi-service integration
- Track mapping between services
"""

import uuid
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
import sqlalchemy
from typing import List, Dict, Optional

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

musicmatch_api_bp = Blueprint('musicmatch_api', __name__)


@musicmatch_api_bp.route('/<recording_mbid>/services', methods=['GET', 'OPTIONS'])
@crossdomain()
@ratelimit()
def get_track_services(recording_mbid: str):
    """
    Get available service IDs for a track by MusicBrainz Recording ID

    Example response:
    {
        "recording_mbid": "3n3...",
        "services": {
            "spotify": "3n3Ppam7vgaVa1iaRUc9Lp",
            "youtube": "dQw4w9WgXcQ",
            "apple_music": "1234567890",
            "tidal": "12345678"
        }
    }

    :param recording_mbid: MusicBrainz Recording MBID
    :statuscode 200: Success
    :statuscode 400: Invalid MBID format
    :statuscode 404: Recording not found in mappings
    :statuscode 500: Internal server error
    """
    try:
        # Validate MBID format
        try:
            uuid.UUID(recording_mbid)
        except ValueError:
            raise APIBadRequest(f"Invalid recording MBID format: {recording_mbid}")

        # Query track_service_mapping table
        query = """
            SELECT service, external_track_id, confidence
              FROM musicmatch.track_service_mapping
             WHERE recording_mbid = :recording_mbid
          ORDER BY confidence DESC
        """

        result = db_conn.execute(
            sqlalchemy.text(query),
            {"recording_mbid": recording_mbid}
        )

        services = {}
        for row in result:
            services[row.service] = {
                "id": row.external_track_id,
                "confidence": float(row.confidence) if row.confidence else None
            }

        if not services:
            raise APINotFound(f"No service mappings found for recording {recording_mbid}")

        return jsonify({
            "recording_mbid": recording_mbid,
            "services": services
        })

    except APIBadRequest:
        raise
    except APINotFound:
        raise
    except Exception as e:
        current_app.logger.error(f"Error fetching track services for {recording_mbid}: {e}", exc_info=True)
        raise APIInternalServerError("Failed to fetch track services")


@musicmatch_api_bp.route('/resolve', methods=['POST', 'OPTIONS'])
@crossdomain()
@ratelimit()
def resolve_track():
    """
    Resolve a track across multiple services using fuzzy matching

    Request body:
    {
        "track_name": "Bohemian Rhapsody",
        "artist_name": "Queen",
        "services": ["spotify", "tidal", "youtube_music"],
        "recording_mbid": "optional-mbid-if-known"
    }

    Response:
    {
        "track_name": "Bohemian Rhapsody",
        "artist_name": "Queen",
        "recording_mbid": "uuid-if-found",
        "matches": {
            "spotify": {
                "id": "3n3Ppam7vgaVa1iaRUc9Lp",
                "confidence": 0.95,
                "track_name": "Bohemian Rhapsody - Remastered 2011",
                "artist_name": "Queen"
            },
            "tidal": {
                "id": "12345678",
                "confidence": 0.92,
                "track_name": "Bohemian Rhapsody",
                "artist_name": "Queen"
            }
        }
    }

    :statuscode 200: Success
    :statuscode 400: Missing required parameters
    :statuscode 500: Internal server error
    """
    try:
        data = request.json
        if not data:
            raise APIBadRequest("Missing request body")

        track_name = data.get('track_name')
        artist_name = data.get('artist_name')
        services = data.get('services', [])
        recording_mbid = data.get('recording_mbid')

        if not track_name or not artist_name:
            raise APIBadRequest("Missing required parameters: track_name and artist_name")

        if not services:
            raise APIBadRequest("At least one service must be specified")

        # Validate service names
        valid_services = {s.value for s in ExternalServiceType}
        for service in services:
            if service not in valid_services:
                raise APIBadRequest(f"Invalid service: {service}")

        matches = {}

        # If MBID is provided, first check if we have existing mappings
        if recording_mbid:
            try:
                uuid.UUID(recording_mbid)
                query = """
                    SELECT service, external_track_id, confidence
                      FROM musicmatch.track_service_mapping
                     WHERE recording_mbid = :recording_mbid
                       AND service = ANY(:services)
                """
                result = db_conn.execute(
                    sqlalchemy.text(query),
                    {"recording_mbid": recording_mbid, "services": services}
                )

                for row in result:
                    matches[row.service] = {
                        "id": row.external_track_id,
                        "confidence": float(row.confidence) if row.confidence else None,
                        "source": "database"
                    }
            except ValueError:
                current_app.logger.warning(f"Invalid MBID format provided: {recording_mbid}")

        # For services not in database, perform API lookups
        # This is a placeholder - actual implementation would call service APIs
        for service in services:
            if service not in matches:
                # TODO: Implement actual service API calls for track resolution
                # For now, we'll just return a placeholder
                matches[service] = {
                    "id": None,
                    "confidence": None,
                    "source": "not_implemented",
                    "message": "Service API integration not yet implemented"
                }

        return jsonify({
            "track_name": track_name,
            "artist_name": artist_name,
            "recording_mbid": recording_mbid,
            "matches": matches
        })

    except APIBadRequest:
        raise
    except Exception as e:
        current_app.logger.error(f"Error resolving track: {e}", exc_info=True)
        raise APIInternalServerError("Failed to resolve track")


@musicmatch_api_bp.route('/mapping', methods=['POST', 'OPTIONS'])
@crossdomain()
@ratelimit()
@login_required
def save_track_mapping():
    """
    Save a track mapping for a recording MBID to an external service

    Request body:
    {
        "recording_mbid": "uuid",
        "service": "spotify",
        "external_track_id": "3n3Ppam7vgaVa1iaRUc9Lp",
        "confidence": 1.0
    }

    :statuscode 200: Success
    :statuscode 400: Missing required parameters or invalid format
    :statuscode 401: Unauthorized
    :statuscode 500: Internal server error
    """
    try:
        data = request.json
        if not data:
            raise APIBadRequest("Missing request body")

        recording_mbid = data.get('recording_mbid')
        service = data.get('service')
        external_track_id = data.get('external_track_id')
        confidence = data.get('confidence', 1.0)

        if not all([recording_mbid, service, external_track_id]):
            raise APIBadRequest("Missing required parameters: recording_mbid, service, external_track_id")

        # Validate MBID
        try:
            uuid.UUID(recording_mbid)
        except ValueError:
            raise APIBadRequest(f"Invalid recording MBID format: {recording_mbid}")

        # Validate service
        try:
            ExternalServiceType(service)
        except ValueError:
            raise APIBadRequest(f"Invalid service: {service}")

        # Validate confidence
        try:
            confidence = float(confidence)
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("Confidence must be between 0.0 and 1.0")
        except (ValueError, TypeError) as e:
            raise APIBadRequest(f"Invalid confidence value: {e}")

        # Insert or update mapping
        query = """
            INSERT INTO musicmatch.track_service_mapping
                (recording_mbid, service, external_track_id, confidence, last_verified)
            VALUES
                (:recording_mbid, :service, :external_track_id, :confidence, NOW())
            ON CONFLICT (recording_mbid, service)
            DO UPDATE SET
                external_track_id = EXCLUDED.external_track_id,
                confidence = EXCLUDED.confidence,
                last_verified = NOW()
        """

        db_conn.execute(
            sqlalchemy.text(query),
            {
                "recording_mbid": recording_mbid,
                "service": service,
                "external_track_id": external_track_id,
                "confidence": confidence
            }
        )
        db_conn.commit()

        return jsonify({
            "success": True,
            "message": "Track mapping saved successfully"
        })

    except APIBadRequest:
        raise
    except Exception as e:
        current_app.logger.error(f"Error saving track mapping: {e}", exc_info=True)
        db_conn.rollback()
        raise APIInternalServerError("Failed to save track mapping")


@musicmatch_api_bp.route('/stats', methods=['GET', 'OPTIONS'])
@crossdomain()
@ratelimit()
def get_musicmatch_stats():
    """
    Get statistics about MusicMatch track mappings

    Response:
    {
        "total_mappings": 1000000,
        "mappings_by_service": {
            "spotify": 850000,
            "tidal": 450000,
            "youtube_music": 600000
        },
        "unique_recordings": 500000
    }

    :statuscode 200: Success
    :statuscode 500: Internal server error
    """
    try:
        # Get total mappings
        total_query = """
            SELECT COUNT(*) as total
              FROM musicmatch.track_service_mapping
        """
        total_result = db_conn.execute(sqlalchemy.text(total_query))
        total_mappings = total_result.fetchone().total

        # Get mappings by service
        service_query = """
            SELECT service, COUNT(*) as count
              FROM musicmatch.track_service_mapping
          GROUP BY service
        """
        service_result = db_conn.execute(sqlalchemy.text(service_query))
        mappings_by_service = {row.service: row.count for row in service_result}

        # Get unique recordings
        unique_query = """
            SELECT COUNT(DISTINCT recording_mbid) as unique_count
              FROM musicmatch.track_service_mapping
        """
        unique_result = db_conn.execute(sqlalchemy.text(unique_query))
        unique_recordings = unique_result.fetchone().unique_count

        return jsonify({
            "total_mappings": total_mappings,
            "mappings_by_service": mappings_by_service,
            "unique_recordings": unique_recordings
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching MusicMatch stats: {e}", exc_info=True)
        raise APIInternalServerError("Failed to fetch statistics")
