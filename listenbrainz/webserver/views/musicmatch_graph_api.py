"""
MusicMatch Graph API Blueprint

Provides endpoints for music graph visualization and exploration
"""

import uuid
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from typing import Optional

from listenbrainz.background.graph_generator import (
    UserMusicGraphGenerator,
    get_cached_graph,
    get_artist_relationship_graph,
    GenreGraph
)
from listenbrainz.webserver.decorators import crossdomain
from listenbrainz.webserver.errors import (
    APIBadRequest,
    APINotFound,
    APIInternalServerError,
    APIUnauthorized
)
from listenbrainz.webserver.rate_limiter import ratelimit
import listenbrainz.db.user as db_user
from listenbrainz.webserver import db_conn

musicmatch_graph_api_bp = Blueprint('musicmatch_graph_api', __name__)


@musicmatch_graph_api_bp.route('/user/<user_name>', methods=['GET', 'OPTIONS'])
@crossdomain()
@ratelimit()
def get_user_music_graph(user_name: str):
    """
    Get a user's personalized music graph

    Query parameters:
    - time_range: week, month, year, all_time (default: month)
    - graph_type: artist, track, genre, combined (default: combined)
    - max_artists: maximum artist nodes (default: 50)
    - max_tracks: maximum track nodes (default: 100)
    - use_cache: whether to use cached graph (default: true)

    Example: GET /1/musicmatch/graph/user/rob?time_range=month&graph_type=combined

    Response:
    {
        "nodes": [
            {"id": "artist_123", "type": "artist", "label": "Queen", ...},
            {"id": "track_456", "type": "track", "label": "Bohemian Rhapsody", ...}
        ],
        "edges": [
            {"source": "artist_123", "target": "track_456", "type": "performed", ...}
        ],
        "metadata": {
            "user_id": 1,
            "time_range": "month",
            "generated_at": "2025-11-17T..."
        }
    }

    :param user_name: ListenBrainz username
    :statuscode 200: Success
    :statuscode 400: Invalid parameters
    :statuscode 404: User not found
    :statuscode 500: Internal server error
    """
    try:
        # Get user
        user = db_user.get_by_mb_id(db_conn, user_name)
        if not user:
            raise APINotFound(f"User '{user_name}' not found")

        user_id = user["id"]

        # Parse query parameters
        time_range = request.args.get('time_range', 'month')
        graph_type = request.args.get('graph_type', 'combined')
        max_artists = int(request.args.get('max_artists', 50))
        max_tracks = int(request.args.get('max_tracks', 100))
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'

        # Validate parameters
        valid_time_ranges = ['week', 'month', 'year', 'all_time']
        if time_range not in valid_time_ranges:
            raise APIBadRequest(f"Invalid time_range. Must be one of: {', '.join(valid_time_ranges)}")

        valid_graph_types = ['artist', 'track', 'genre', 'combined']
        if graph_type not in valid_graph_types:
            raise APIBadRequest(f"Invalid graph_type. Must be one of: {', '.join(valid_graph_types)}")

        if max_artists < 1 or max_artists > 200:
            raise APIBadRequest("max_artists must be between 1 and 200")

        if max_tracks < 1 or max_tracks > 500:
            raise APIBadRequest("max_tracks must be between 1 and 500")

        # Try to get cached graph first
        if use_cache:
            cached = get_cached_graph(user_id, graph_type, time_range)
            if cached:
                return jsonify(cached)

        # Generate new graph
        generator = UserMusicGraphGenerator(user_id)
        graph_data = generator.generate_graph(
            time_range=time_range,
            max_artists=max_artists,
            max_tracks=max_tracks,
            include_genres=(graph_type in ['genre', 'combined'])
        )

        # Save to cache for future requests
        try:
            generator.save_to_database(graph_type=graph_type, time_range=time_range)
        except Exception as e:
            current_app.logger.warning(f"Failed to cache graph: {e}")

        return jsonify(graph_data)

    except APIBadRequest:
        raise
    except APINotFound:
        raise
    except Exception as e:
        current_app.logger.error(f"Error generating user graph for {user_name}: {e}", exc_info=True)
        raise APIInternalServerError("Failed to generate user music graph")


@musicmatch_graph_api_bp.route('/artist/<artist_mbid>', methods=['GET', 'OPTIONS'])
@crossdomain()
@ratelimit()
def get_artist_graph(artist_mbid: str):
    """
    Get an artist relationship graph

    Query parameters:
    - depth: relationship depth 1-3 (default: 2)
    - max_related: maximum related artists per level (default: 20)

    Example: GET /1/musicmatch/graph/artist/5b11f4ce-a62d-471e-81fc-a69a8278c7da?depth=2

    Response:
    {
        "nodes": [
            {"id": "artist_5b11...", "type": "artist", "label": "Nirvana", "is_root": true, ...},
            {"id": "artist_8bfac...", "type": "artist", "label": "Foo Fighters", ...}
        ],
        "edges": [
            {"source": "artist_5b11...", "target": "artist_8bfac...", "type": "collaboration", ...}
        ],
        "metadata": {
            "root_artist_mbid": "5b11f4ce-a62d-471e-81fc-a69a8278c7da",
            "root_artist_name": "Nirvana",
            "depth": 2
        }
    }

    :param artist_mbid: MusicBrainz Artist MBID
    :statuscode 200: Success
    :statuscode 400: Invalid MBID or parameters
    :statuscode 404: Artist not found
    :statuscode 500: Internal server error
    """
    try:
        # Validate MBID
        try:
            uuid.UUID(artist_mbid)
        except ValueError:
            raise APIBadRequest(f"Invalid artist MBID format: {artist_mbid}")

        # Parse query parameters
        depth = int(request.args.get('depth', 2))
        max_related = int(request.args.get('max_related', 20))

        # Validate parameters
        if depth < 1 or depth > 3:
            raise APIBadRequest("depth must be between 1 and 3")

        if max_related < 1 or max_related > 100:
            raise APIBadRequest("max_related must be between 1 and 100")

        # Generate graph
        graph_data = get_artist_relationship_graph(artist_mbid, depth=depth)

        if not graph_data:
            raise APINotFound(f"Could not generate graph for artist {artist_mbid}")

        return jsonify(graph_data)

    except APIBadRequest:
        raise
    except APINotFound:
        raise
    except Exception as e:
        current_app.logger.error(f"Error generating artist graph for {artist_mbid}: {e}", exc_info=True)
        raise APIInternalServerError("Failed to generate artist relationship graph")


@musicmatch_graph_api_bp.route('/genre', methods=['GET', 'OPTIONS'])
@crossdomain()
@ratelimit()
def get_genre_graph():
    """
    Get a genre relationship graph

    Query parameters:
    - type: hierarchy or landscape (default: landscape)
    - root_genre: starting genre for hierarchy type (optional)
    - max_depth: maximum hierarchy depth (default: 3)
    - min_popularity: minimum popularity for landscape (default: 100)

    Example: GET /1/musicmatch/graph/genre?type=hierarchy&root_genre=rock&max_depth=2

    Response:
    {
        "nodes": [
            {"id": "genre_rock", "type": "genre", "label": "rock", "weight": 1500, ...},
            {"id": "genre_alternative rock", "type": "genre", "label": "alternative rock", ...}
        ],
        "edges": [
            {"source": "genre_rock", "target": "genre_alternative rock", "type": "parent_of", ...}
        ],
        "metadata": {
            "type": "hierarchy",
            "root_genre": "rock",
            "max_depth": 2
        }
    }

    :statuscode 200: Success
    :statuscode 400: Invalid parameters
    :statuscode 500: Internal server error
    """
    try:
        # Parse query parameters
        graph_type = request.args.get('type', 'landscape')
        root_genre = request.args.get('root_genre')
        max_depth = int(request.args.get('max_depth', 3))
        min_popularity = int(request.args.get('min_popularity', 100))

        # Validate parameters
        valid_types = ['hierarchy', 'landscape']
        if graph_type not in valid_types:
            raise APIBadRequest(f"Invalid type. Must be one of: {', '.join(valid_types)}")

        if max_depth < 1 or max_depth > 5:
            raise APIBadRequest("max_depth must be between 1 and 5")

        if min_popularity < 0:
            raise APIBadRequest("min_popularity must be non-negative")

        # Generate graph
        generator = GenreGraph()

        if graph_type == 'hierarchy':
            graph_data = generator.generate_genre_hierarchy(
                root_genre=root_genre,
                max_depth=max_depth
            )
        else:  # landscape
            graph_data = generator.generate_genre_landscape(
                min_popularity=min_popularity
            )

        return jsonify(graph_data)

    except APIBadRequest:
        raise
    except Exception as e:
        current_app.logger.error(f"Error generating genre graph: {e}", exc_info=True)
        raise APIInternalServerError("Failed to generate genre graph")


@musicmatch_graph_api_bp.route('/user/<user_name>/genre/<genre_name>', methods=['GET', 'OPTIONS'])
@crossdomain()
@ratelimit()
def get_user_genre_exploration(user_name: str, genre_name: str):
    """
    Get a user's exploration of a specific genre

    Shows the user's top artists and tracks in a genre, and how they relate to the genre

    Query parameters:
    - time_range: week, month, year, all_time (default: month)
    - max_items: maximum items to return (default: 30)

    :param user_name: ListenBrainz username
    :param genre_name: Genre name
    :statuscode 200: Success
    :statuscode 404: User not found
    :statuscode 500: Internal server error
    """
    try:
        # Get user
        user = db_user.get_by_mb_id(db_conn, user_name)
        if not user:
            raise APINotFound(f"User '{user_name}' not found")

        user_id = user["id"]

        # Parse parameters
        time_range = request.args.get('time_range', 'month')
        max_items = int(request.args.get('max_items', 30))

        # TODO: Implement genre-specific user exploration
        # This would combine user listening data with genre information

        return jsonify({
            "user_name": user_name,
            "genre_name": genre_name,
            "time_range": time_range,
            "nodes": [],
            "edges": [],
            "metadata": {
                "message": "Genre exploration not yet implemented"
            }
        })

    except APINotFound:
        raise
    except Exception as e:
        current_app.logger.error(f"Error generating user genre exploration: {e}", exc_info=True)
        raise APIInternalServerError("Failed to generate user genre exploration")
