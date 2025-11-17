"""
User Music Graph Generator

Generates personalized music graphs for users based on their listening history.
The graph includes nodes for artists, tracks, and genres, with edges representing
relationships and listening patterns.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlalchemy
from flask import current_app

from listenbrainz.webserver import db_conn, ts_conn


class UserMusicGraphGenerator:
    """Generates music graphs for individual users based on listening history"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.graph_data = {
            "nodes": [],
            "edges": [],
            "metadata": {}
        }

    def generate_graph(
        self,
        time_range: str = "month",
        max_artists: int = 50,
        max_tracks: int = 100,
        include_genres: bool = True
    ) -> Dict:
        """
        Generate a complete user music graph

        Args:
            time_range: Time range for data ('week', 'month', 'year', 'all_time')
            max_artists: Maximum number of artist nodes to include
            max_tracks: Maximum number of track nodes to include
            include_genres: Whether to include genre nodes

        Returns:
            Graph data dictionary with nodes and edges
        """
        time_ranges = {
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "year": timedelta(days=365),
            "all_time": None
        }

        if time_range not in time_ranges:
            raise ValueError(f"Invalid time_range: {time_range}")

        time_delta = time_ranges[time_range]

        # Get user's top artists
        top_artists = self._get_top_artists(time_delta, max_artists)

        # Get user's top tracks
        top_tracks = self._get_top_tracks(time_delta, max_tracks)

        # Build nodes
        self._build_artist_nodes(top_artists)
        self._build_track_nodes(top_tracks)

        if include_genres:
            genres = self._extract_genres_from_artists(top_artists)
            self._build_genre_nodes(genres)

        # Build edges
        self._build_artist_track_edges(top_tracks)

        if include_genres:
            self._build_artist_genre_edges(top_artists)
            self._build_track_genre_edges(top_tracks)

        # Add metadata
        self.graph_data["metadata"] = {
            "user_id": self.user_id,
            "time_range": time_range,
            "generated_at": datetime.now().isoformat(),
            "node_count": len(self.graph_data["nodes"]),
            "edge_count": len(self.graph_data["edges"])
        }

        return self.graph_data

    def _get_top_artists(self, time_delta: Optional[timedelta], limit: int) -> List[Dict]:
        """Get user's top artists for the time period"""
        query = """
            SELECT artist_name,
                   artist_mbids[1] as artist_mbid,
                   COUNT(*) as listen_count
              FROM listen
             WHERE user_id = :user_id
        """

        params = {"user_id": self.user_id, "limit": limit}

        if time_delta:
            since = datetime.now() - time_delta
            query += " AND listened_at >= :since"
            params["since"] = since

        query += """
          GROUP BY artist_name, artist_mbids[1]
          ORDER BY listen_count DESC
             LIMIT :limit
        """

        try:
            result = ts_conn.execute(sqlalchemy.text(query), params)
            return [
                {
                    "name": row.artist_name,
                    "mbid": row.artist_mbid,
                    "listen_count": row.listen_count
                }
                for row in result
            ]
        except Exception as e:
            current_app.logger.error(f"Error fetching top artists for user {self.user_id}: {e}")
            return []

    def _get_top_tracks(self, time_delta: Optional[timedelta], limit: int) -> List[Dict]:
        """Get user's top tracks for the time period"""
        query = """
            SELECT track_name,
                   artist_name,
                   recording_mbid,
                   artist_mbids[1] as artist_mbid,
                   COUNT(*) as listen_count
              FROM listen
             WHERE user_id = :user_id
        """

        params = {"user_id": self.user_id, "limit": limit}

        if time_delta:
            since = datetime.now() - time_delta
            query += " AND listened_at >= :since"
            params["since"] = since

        query += """
          GROUP BY track_name, artist_name, recording_mbid, artist_mbids[1]
          ORDER BY listen_count DESC
             LIMIT :limit
        """

        try:
            result = ts_conn.execute(sqlalchemy.text(query), params)
            return [
                {
                    "name": row.track_name,
                    "artist_name": row.artist_name,
                    "recording_mbid": str(row.recording_mbid) if row.recording_mbid else None,
                    "artist_mbid": row.artist_mbid,
                    "listen_count": row.listen_count
                }
                for row in result
            ]
        except Exception as e:
            current_app.logger.error(f"Error fetching top tracks for user {self.user_id}: {e}")
            return []

    def _extract_genres_from_artists(self, artists: List[Dict]) -> Dict[str, int]:
        """Extract genres from artists with their weights"""
        # Placeholder - would need to query musicbrainz tags/genres
        # For now, return empty dict
        # TODO: Implement actual genre extraction from MB tags
        return {}

    def _build_artist_nodes(self, artists: List[Dict]):
        """Build artist nodes for the graph"""
        for artist in artists:
            node = {
                "id": f"artist_{artist['mbid'] or artist['name']}",
                "type": "artist",
                "label": artist["name"],
                "mbid": artist["mbid"],
                "weight": artist["listen_count"],
                "metadata": {
                    "listen_count": artist["listen_count"]
                }
            }
            self.graph_data["nodes"].append(node)

    def _build_track_nodes(self, tracks: List[Dict]):
        """Build track nodes for the graph"""
        for track in tracks:
            node = {
                "id": f"track_{track['recording_mbid'] or track['name']}",
                "type": "track",
                "label": track["name"],
                "mbid": track["recording_mbid"],
                "weight": track["listen_count"],
                "metadata": {
                    "artist_name": track["artist_name"],
                    "listen_count": track["listen_count"]
                }
            }
            self.graph_data["nodes"].append(node)

    def _build_genre_nodes(self, genres: Dict[str, int]):
        """Build genre nodes for the graph"""
        for genre_name, weight in genres.items():
            node = {
                "id": f"genre_{genre_name}",
                "type": "genre",
                "label": genre_name,
                "weight": weight,
                "metadata": {
                    "count": weight
                }
            }
            self.graph_data["nodes"].append(node)

    def _build_artist_track_edges(self, tracks: List[Dict]):
        """Build edges between artists and tracks"""
        for track in tracks:
            edge = {
                "source": f"artist_{track['artist_mbid'] or track['artist_name']}",
                "target": f"track_{track['recording_mbid'] or track['name']}",
                "type": "performed",
                "weight": track["listen_count"]
            }
            self.graph_data["edges"].append(edge)

    def _build_artist_genre_edges(self, artists: List[Dict]):
        """Build edges between artists and genres"""
        # Placeholder - would connect artists to their genres
        # TODO: Implement with actual genre data
        pass

    def _build_track_genre_edges(self, tracks: List[Dict]):
        """Build edges between tracks and genres"""
        # Placeholder - would connect tracks to their genres
        # TODO: Implement with actual genre data
        pass

    def save_to_database(self, graph_type: str = "combined", time_range: str = "month"):
        """
        Save generated graph to database for caching

        Args:
            graph_type: Type of graph ('artist', 'track', 'genre', 'combined')
            time_range: Time range for the graph
        """
        query = """
            INSERT INTO musicmatch.user_music_graph
                (user_id, graph_type, time_range, graph_data, generated_at)
            VALUES
                (:user_id, :graph_type, :time_range, :graph_data, NOW())
            ON CONFLICT (user_id, graph_type, time_range)
            DO UPDATE SET
                graph_data = EXCLUDED.graph_data,
                generated_at = NOW()
        """

        try:
            db_conn.execute(
                sqlalchemy.text(query),
                {
                    "user_id": self.user_id,
                    "graph_type": graph_type,
                    "time_range": time_range,
                    "graph_data": json.dumps(self.graph_data)
                }
            )
            db_conn.commit()
            current_app.logger.info(
                f"Saved {graph_type} graph for user {self.user_id} ({time_range})"
            )
        except Exception as e:
            current_app.logger.error(
                f"Error saving graph for user {self.user_id}: {e}",
                exc_info=True
            )
            db_conn.rollback()


def get_cached_graph(user_id: int, graph_type: str, time_range: str) -> Optional[Dict]:
    """
    Retrieve cached graph from database

    Args:
        user_id: User ID
        graph_type: Type of graph
        time_range: Time range

    Returns:
        Graph data if found, None otherwise
    """
    query = """
        SELECT graph_data, generated_at
          FROM musicmatch.user_music_graph
         WHERE user_id = :user_id
           AND graph_type = :graph_type
           AND time_range = :time_range
    """

    try:
        result = db_conn.execute(
            sqlalchemy.text(query),
            {
                "user_id": user_id,
                "graph_type": graph_type,
                "time_range": time_range
            }
        ).fetchone()

        if result:
            graph_data = json.loads(result.graph_data)
            graph_data["metadata"]["cached_at"] = result.generated_at.isoformat()
            return graph_data

        return None
    except Exception as e:
        current_app.logger.error(f"Error retrieving cached graph: {e}")
        return None
