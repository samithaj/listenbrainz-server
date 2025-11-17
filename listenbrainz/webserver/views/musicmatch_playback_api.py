"""
MusicMatch Playback API

Unified playback API endpoints for multi-service playback control
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from listenbrainz.background.playback.playback_router import PlaybackRouter, PlaybackState
from listenbrainz.background.playback.service_players.spotify_player import SpotifyPlayer
from listenbrainz.background.playback.service_players.tidal_player import TidalPlayer
from listenbrainz.background.playback.service_players.youtube_music_player import YoutubeMusicPlayer
from listenbrainz.background.playback.service_players.apple_music_player import AppleMusicPlayer
from listenbrainz.db import musicmatch as db_musicmatch
from listenbrainz.webserver.decorators import crossdomain
from listenbrainz.webserver.rate_limiter import ratelimit


musicmatch_playback_api_bp = Blueprint("musicmatch_playback_api", __name__)


def get_player_for_service(user_id: int, service: str):
    """
    Get the appropriate player instance for a service

    Args:
        user_id: User ID
        service: Service name

    Returns:
        Player instance or None
    """
    players = {
        "spotify": SpotifyPlayer,
        "tidal": TidalPlayer,
        "youtube_music": YoutubeMusicPlayer,
        "apple": AppleMusicPlayer,
    }

    player_class = players.get(service)
    if player_class:
        return player_class(user_id)

    return None


@musicmatch_playback_api_bp.route("/play", methods=["POST", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def play_track():
    """
    Start playback of a track

    Request body:
    {
        "recording_mbid": "uuid",
        "preferred_service": "spotify"  // optional
    }

    Returns:
        {
            "success": true,
            "session_id": "uuid",
            "service": "spotify",
            "external_track_id": "..."
        }
    """
    data = request.json

    if not data or "recording_mbid" not in data:
        return jsonify({"error": "recording_mbid is required"}), 400

    recording_mbid = data["recording_mbid"]
    preferred_service = data.get("preferred_service")

    # Initialize playback router
    router = PlaybackRouter(current_user.id)

    # Select best service for playback
    service, external_track_id = router.select_playback_service(
        recording_mbid,
        preferred_service=preferred_service
    )

    if not service or not external_track_id:
        return jsonify({
            "error": "Track not available on any connected service"
        }), 404

    # Get player for selected service
    player = get_player_for_service(current_user.id, service)

    if not player:
        return jsonify({"error": f"Player not available for {service}"}), 500

    # Create playback session
    session_id = router.create_session(service)

    # Start playback (if service supports server-side control)
    if player.supports_playback_control():
        success = player.play_track(external_track_id)

        if success:
            router.set_playback_state(PlaybackState.PLAYING, recording_mbid)

            # Record playback
            db_musicmatch.record_playback(
                user_id=current_user.id,
                recording_mbid=recording_mbid,
                service=service,
                duration_ms=0,  # Will be updated when playback ends
                session_id=session_id
            )

            return jsonify({
                "success": True,
                "session_id": session_id,
                "service": service,
                "external_track_id": external_track_id,
                "supports_server_control": True
            })
        else:
            return jsonify({
                "error": "Failed to start playback",
                "session_id": session_id,
                "service": service
            }), 500
    else:
        # Service requires client-side control
        return jsonify({
            "success": True,
            "session_id": session_id,
            "service": service,
            "external_track_id": external_track_id,
            "supports_server_control": False,
            "requires_client_sdk": True
        })


@musicmatch_playback_api_bp.route("/pause", methods=["POST", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def pause_playback():
    """Pause current playback"""
    # Get active session
    session = db_musicmatch.get_active_session(current_user.id)

    if not session:
        return jsonify({"error": "No active playback session"}), 404

    service = session["service"]
    player = get_player_for_service(current_user.id, service)

    if not player or not player.supports_playback_control():
        return jsonify({
            "error": f"{service} requires client-side control"
        }), 400

    success = player.pause()

    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to pause playback"}), 500


@musicmatch_playback_api_bp.route("/resume", methods=["POST", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def resume_playback():
    """Resume paused playback"""
    session = db_musicmatch.get_active_session(current_user.id)

    if not session:
        return jsonify({"error": "No active playback session"}), 404

    service = session["service"]
    player = get_player_for_service(current_user.id, service)

    if not player or not player.supports_playback_control():
        return jsonify({
            "error": f"{service} requires client-side control"
        }), 400

    success = player.resume()

    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to resume playback"}), 500


@musicmatch_playback_api_bp.route("/skip", methods=["POST", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def skip_track():
    """Skip to next track in queue"""
    session = db_musicmatch.get_active_session(current_user.id)

    if not session:
        return jsonify({"error": "No active playback session"}), 404

    service = session["service"]
    player = get_player_for_service(current_user.id, service)

    if not player or not player.supports_playback_control():
        return jsonify({
            "error": f"{service} requires client-side control"
        }), 400

    success = player.skip_to_next()

    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to skip track"}), 500


@musicmatch_playback_api_bp.route("/status", methods=["GET", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def get_playback_status():
    """
    Get current playback status

    Returns:
        {
            "session": {...},
            "playback_state": {...},
            "queue": [...]
        }
    """
    session = db_musicmatch.get_active_session(current_user.id)

    if not session:
        return jsonify({
            "session": None,
            "playback_state": None,
            "queue": []
        })

    service = session["service"]
    session_id = session["session_id"]

    # Get playback state from player (if supported)
    player = get_player_for_service(current_user.id, service)
    playback_state = None

    if player and player.supports_playback_control():
        playback_state = player.get_playback_state()

    # Get queue
    queue = db_musicmatch.get_playback_queue(session_id)

    return jsonify({
        "session": session,
        "playback_state": playback_state,
        "queue": queue,
        "supports_server_control": player.supports_playback_control() if player else False
    })


@musicmatch_playback_api_bp.route("/queue", methods=["POST", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def add_to_queue():
    """
    Add track(s) to playback queue

    Request body:
    {
        "recording_mbids": ["uuid1", "uuid2", ...]
    }
    """
    data = request.json

    if not data or "recording_mbids" not in data:
        return jsonify({"error": "recording_mbids is required"}), 400

    recording_mbids = data["recording_mbids"]

    if not isinstance(recording_mbids, list):
        return jsonify({"error": "recording_mbids must be an array"}), 400

    # Get or create session
    session = db_musicmatch.get_active_session(current_user.id)

    if not session:
        # Create a new session with default service (Spotify)
        router = PlaybackRouter(current_user.id)
        connected_services = router.get_user_connected_services()

        if not connected_services:
            return jsonify({"error": "No connected services"}), 400

        # Use first connected service
        service = connected_services[0]
        session_id = router.create_session(service)
    else:
        session_id = session["session_id"]
        service = session["service"]

    # Get current queue length
    current_queue = db_musicmatch.get_playback_queue(session_id)
    position = len(current_queue)

    # Add tracks to queue
    for mbid in recording_mbids:
        db_musicmatch.add_to_playback_queue(session_id, mbid, position)
        position += 1

    # If service supports it, also add to service's queue
    player = get_player_for_service(current_user.id, service)

    if player and player.supports_playback_control():
        for mbid in recording_mbids:
            services = db_musicmatch.get_track_services(mbid)
            external_track_id = services.get(service)

            if external_track_id:
                player.add_to_queue(external_track_id)

    return jsonify({
        "success": True,
        "session_id": session_id,
        "tracks_added": len(recording_mbids)
    })


@musicmatch_playback_api_bp.route("/queue", methods=["GET", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def get_queue():
    """Get current playback queue"""
    session = db_musicmatch.get_active_session(current_user.id)

    if not session:
        return jsonify({"queue": []})

    queue = db_musicmatch.get_playback_queue(session["session_id"])

    return jsonify({"queue": queue})


@musicmatch_playback_api_bp.route("/history", methods=["GET", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def get_history():
    """
    Get playback history

    Query params:
        limit: Max results (default: 50)
        offset: Results to skip (default: 0)
    """
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    # Clamp limit
    limit = min(limit, 100)

    history = db_musicmatch.get_playback_history(
        current_user.id,
        limit=limit,
        offset=offset
    )

    return jsonify({
        "history": history,
        "limit": limit,
        "offset": offset
    })


@musicmatch_playback_api_bp.route("/stats", methods=["GET", "OPTIONS"])
@crossdomain
@ratelimit()
@login_required
def get_stats():
    """Get playback statistics"""
    stats = db_musicmatch.get_playback_stats(current_user.id)

    return jsonify({"stats": stats})
