"""
Database functions for MusicMatch feature
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid

import sqlalchemy
from listenbrainz import db


def get_track_services(recording_mbid: str) -> Dict[str, str]:
    """
    Get available services for a track

    Args:
        recording_mbid: MusicBrainz recording ID

    Returns:
        Dict mapping service name to external track ID
    """
    query = sqlalchemy.text("""
        SELECT service, external_track_id
        FROM musicmatch.track_service_mapping
        WHERE recording_mbid = :mbid
    """)

    with db.engine.connect() as connection:
        result = connection.execute(query, {"mbid": recording_mbid})
        return {row.service: row.external_track_id for row in result}


def create_playback_session(session_id: str, user_id: int, service: str):
    """
    Create a new playback session

    Args:
        session_id: UUID for the session
        user_id: ListenBrainz user ID
        service: Service name (spotify, tidal, etc.)
    """
    query = sqlalchemy.text("""
        INSERT INTO musicmatch.playback_sessions (session_id, user_id, service)
        VALUES (:session_id, :user_id, :service)
    """)

    with db.engine.connect() as connection:
        connection.execute(query, {
            "session_id": session_id,
            "user_id": user_id,
            "service": service
        })
        connection.commit()


def end_playback_session(session_id: str):
    """
    End a playback session

    Args:
        session_id: Session UUID
    """
    query = sqlalchemy.text("""
        UPDATE musicmatch.playback_sessions
        SET ended_at = NOW()
        WHERE session_id = :session_id
    """)

    with db.engine.connect() as connection:
        connection.execute(query, {"session_id": session_id})
        connection.commit()


def get_active_session(user_id: int) -> Optional[Dict]:
    """
    Get user's active playback session

    Args:
        user_id: ListenBrainz user ID

    Returns:
        Session dict or None
    """
    query = sqlalchemy.text("""
        SELECT session_id, service, started_at
        FROM musicmatch.playback_sessions
        WHERE user_id = :user_id AND ended_at IS NULL
        ORDER BY started_at DESC
        LIMIT 1
    """)

    with db.engine.connect() as connection:
        result = connection.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if row:
            return {
                "session_id": str(row.session_id),
                "service": row.service,
                "started_at": row.started_at.isoformat()
            }

        return None


def add_to_playback_queue(session_id: str, recording_mbid: str, position: int):
    """
    Add track to playback queue

    Args:
        session_id: Session UUID
        recording_mbid: MusicBrainz recording ID
        position: Position in queue
    """
    query = sqlalchemy.text("""
        INSERT INTO musicmatch.playback_queue (session_id, recording_mbid, position)
        VALUES (:session_id, :mbid, :position)
        ON CONFLICT (session_id, position)
        DO UPDATE SET recording_mbid = :mbid
    """)

    with db.engine.connect() as connection:
        connection.execute(query, {
            "session_id": session_id,
            "mbid": recording_mbid,
            "position": position
        })
        connection.commit()


def get_playback_queue(session_id: str) -> List[Dict]:
    """
    Get playback queue for a session

    Args:
        session_id: Session UUID

    Returns:
        List of queue items
    """
    query = sqlalchemy.text("""
        SELECT position, recording_mbid, added_at, played_at
        FROM musicmatch.playback_queue
        WHERE session_id = :session_id
        ORDER BY position
    """)

    with db.engine.connect() as connection:
        result = connection.execute(query, {"session_id": session_id})

        return [
            {
                "position": row.position,
                "recording_mbid": str(row.recording_mbid),
                "added_at": row.added_at.isoformat(),
                "played_at": row.played_at.isoformat() if row.played_at else None
            }
            for row in result
        ]


def mark_track_played(session_id: str, recording_mbid: str):
    """
    Mark a track as played in the queue

    Args:
        session_id: Session UUID
        recording_mbid: MusicBrainz recording ID
    """
    query = sqlalchemy.text("""
        UPDATE musicmatch.playback_queue
        SET played_at = NOW()
        WHERE session_id = :session_id AND recording_mbid = :mbid
    """)

    with db.engine.connect() as connection:
        connection.execute(query, {
            "session_id": session_id,
            "mbid": recording_mbid
        })
        connection.commit()


def record_playback(
    user_id: int,
    recording_mbid: str,
    service: str,
    duration_ms: int,
    session_id: Optional[str] = None
):
    """
    Record a track playback to history

    Args:
        user_id: ListenBrainz user ID
        recording_mbid: MusicBrainz recording ID
        service: Service name
        duration_ms: Duration played in milliseconds
        session_id: Optional session UUID
    """
    query = sqlalchemy.text("""
        INSERT INTO musicmatch.playback_history
        (user_id, recording_mbid, service, duration_ms, session_id)
        VALUES (:user_id, :mbid, :service, :duration_ms, :session_id)
    """)

    with db.engine.connect() as connection:
        connection.execute(query, {
            "user_id": user_id,
            "mbid": recording_mbid,
            "service": service,
            "duration_ms": duration_ms,
            "session_id": session_id
        })
        connection.commit()


def get_playback_history(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    Get user's playback history

    Args:
        user_id: ListenBrainz user ID
        limit: Maximum results to return
        offset: Number of results to skip

    Returns:
        List of playback history items
    """
    query = sqlalchemy.text("""
        SELECT recording_mbid, service, played_at, duration_ms, session_id
        FROM musicmatch.playback_history
        WHERE user_id = :user_id
        ORDER BY played_at DESC
        LIMIT :limit OFFSET :offset
    """)

    with db.engine.connect() as connection:
        result = connection.execute(query, {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        })

        return [
            {
                "recording_mbid": str(row.recording_mbid),
                "service": row.service,
                "played_at": row.played_at.isoformat(),
                "duration_ms": row.duration_ms,
                "session_id": str(row.session_id) if row.session_id else None
            }
            for row in result
        ]


def get_playback_stats(user_id: int) -> Dict:
    """
    Get playback statistics for a user

    Args:
        user_id: ListenBrainz user ID

    Returns:
        Dict with playback statistics
    """
    query = sqlalchemy.text("""
        SELECT
            COUNT(*) as total_plays,
            COUNT(DISTINCT recording_mbid) as unique_tracks,
            COUNT(DISTINCT service) as services_used,
            SUM(duration_ms) as total_duration_ms
        FROM musicmatch.playback_history
        WHERE user_id = :user_id
    """)

    with db.engine.connect() as connection:
        result = connection.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if row:
            return {
                "total_plays": row.total_plays,
                "unique_tracks": row.unique_tracks,
                "services_used": row.services_used,
                "total_duration_ms": row.total_duration_ms or 0
            }

        return {
            "total_plays": 0,
            "unique_tracks": 0,
            "services_used": 0,
            "total_duration_ms": 0
        }
