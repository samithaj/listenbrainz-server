"""
Genre Graph Generator

Generates graphs showing genre relationships, hierarchies, and connections to artists/tracks.
"""

import json
from typing import Dict, List, Optional, Set, Tuple
import sqlalchemy
from flask import current_app
from collections import defaultdict

from listenbrainz.webserver import db_conn, ts_conn


class GenreGraph:
    """Generates genre relationship and hierarchy graphs"""

    def __init__(self):
        self.graph_data = {
            "nodes": [],
            "edges": [],
            "metadata": {}
        }
        self.genre_hierarchy = {}
        self.processed_genres: Set[str] = set()

    def generate_genre_hierarchy(self, root_genre: Optional[str] = None, max_depth: int = 3) -> Dict:
        """
        Generate a genre hierarchy graph

        Args:
            root_genre: Starting genre (None for all top-level genres)
            max_depth: Maximum depth of hierarchy to explore

        Returns:
            Graph data with genre nodes and hierarchy edges
        """
        if root_genre:
            self._build_genre_subtree(root_genre, current_depth=0, max_depth=max_depth)
        else:
            # Build from top-level genres
            top_genres = self._get_top_level_genres()
            for genre in top_genres:
                self._build_genre_subtree(genre["name"], current_depth=0, max_depth=max_depth)

        self.graph_data["metadata"] = {
            "root_genre": root_genre,
            "max_depth": max_depth,
            "node_count": len(self.graph_data["nodes"]),
            "edge_count": len(self.graph_data["edges"])
        }

        return self.graph_data

    def generate_genre_landscape(self, min_popularity: int = 100) -> Dict:
        """
        Generate a landscape of popular genres and their relationships

        Args:
            min_popularity: Minimum popularity score to include genre

        Returns:
            Graph data showing genre relationships
        """
        popular_genres = self._get_popular_genres(min_popularity)

        # Add genre nodes
        for genre in popular_genres:
            self._add_genre_node(genre)
            self.processed_genres.add(genre["name"])

        # Build relationships between genres
        self._build_genre_relationships(popular_genres)

        self.graph_data["metadata"] = {
            "type": "landscape",
            "min_popularity": min_popularity,
            "node_count": len(self.graph_data["nodes"]),
            "edge_count": len(self.graph_data["edges"])
        }

        return self.graph_data

    def _get_top_level_genres(self) -> List[Dict]:
        """Get top-level genres (those without a parent)"""
        query = """
            SELECT genre_name as name,
                   popularity_score
              FROM musicmatch.genre_hierarchy
             WHERE parent_genre IS NULL
               AND level = 0
          ORDER BY popularity_score DESC
             LIMIT 20
        """

        try:
            result = db_conn.execute(sqlalchemy.text(query))
            return [
                {
                    "name": row.name,
                    "popularity": float(row.popularity_score) if row.popularity_score else 0.0
                }
                for row in result
            ]
        except Exception as e:
            current_app.logger.error(f"Error fetching top-level genres: {e}")
            return []

    def _get_popular_genres(self, min_popularity: int) -> List[Dict]:
        """Get popular genres above a threshold"""
        query = """
            SELECT genre_name as name,
                   parent_genre,
                   level,
                   popularity_score
              FROM musicmatch.genre_hierarchy
             WHERE popularity_score >= :min_popularity
          ORDER BY popularity_score DESC
             LIMIT 100
        """

        try:
            result = db_conn.execute(
                sqlalchemy.text(query),
                {"min_popularity": min_popularity}
            )
            return [
                {
                    "name": row.name,
                    "parent": row.parent_genre,
                    "level": row.level,
                    "popularity": float(row.popularity_score) if row.popularity_score else 0.0
                }
                for row in result
            ]
        except Exception as e:
            current_app.logger.error(f"Error fetching popular genres: {e}")
            return []

    def _get_child_genres(self, parent_genre: str) -> List[Dict]:
        """Get child genres for a given parent"""
        query = """
            SELECT genre_name as name,
                   level,
                   popularity_score
              FROM musicmatch.genre_hierarchy
             WHERE parent_genre = :parent_genre
          ORDER BY popularity_score DESC
             LIMIT 20
        """

        try:
            result = db_conn.execute(
                sqlalchemy.text(query),
                {"parent_genre": parent_genre}
            )
            return [
                {
                    "name": row.name,
                    "level": row.level,
                    "popularity": float(row.popularity_score) if row.popularity_score else 0.0
                }
                for row in result
            ]
        except Exception as e:
            current_app.logger.error(f"Error fetching child genres: {e}")
            return []

    def _build_genre_subtree(self, genre_name: str, current_depth: int, max_depth: int):
        """Recursively build genre hierarchy tree"""
        if current_depth > max_depth or genre_name in self.processed_genres:
            return

        # Get genre info
        genre_info = self._get_genre_info(genre_name)
        if not genre_info:
            return

        # Add node
        self._add_genre_node(genre_info)
        self.processed_genres.add(genre_name)

        # Get and process children
        if current_depth < max_depth:
            children = self._get_child_genres(genre_name)
            for child in children:
                # Add edge from parent to child
                self._add_edge(
                    genre_name,
                    child["name"],
                    "parent_of",
                    weight=1.0
                )
                # Recurse
                self._build_genre_subtree(
                    child["name"],
                    current_depth + 1,
                    max_depth
                )

    def _get_genre_info(self, genre_name: str) -> Optional[Dict]:
        """Get detailed genre information"""
        query = """
            SELECT genre_name as name,
                   parent_genre,
                   level,
                   popularity_score
              FROM musicmatch.genre_hierarchy
             WHERE genre_name = :genre_name
        """

        try:
            result = db_conn.execute(
                sqlalchemy.text(query),
                {"genre_name": genre_name}
            ).fetchone()

            if result:
                return {
                    "name": result.name,
                    "parent": result.parent_genre,
                    "level": result.level,
                    "popularity": float(result.popularity_score) if result.popularity_score else 0.0
                }
            return None
        except Exception as e:
            current_app.logger.error(f"Error fetching genre info: {e}")
            return None

    def _add_genre_node(self, genre: Dict):
        """Add a genre node to the graph"""
        node = {
            "id": f"genre_{genre['name']}",
            "type": "genre",
            "label": genre["name"],
            "weight": genre.get("popularity", 0.0),
            "metadata": {
                "level": genre.get("level", 0),
                "popularity": genre.get("popularity", 0.0),
                "parent": genre.get("parent")
            }
        }
        self.graph_data["nodes"].append(node)

    def _add_edge(self, source_genre: str, target_genre: str, edge_type: str, weight: float = 1.0):
        """Add an edge between genres"""
        edge = {
            "source": f"genre_{source_genre}",
            "target": f"genre_{target_genre}",
            "type": edge_type,
            "weight": weight
        }
        self.graph_data["edges"].append(edge)

    def _build_genre_relationships(self, genres: List[Dict]):
        """Build relationship edges between genres based on shared characteristics"""
        # Calculate co-occurrence of genres in user listening
        genre_cooccurrence = self._calculate_genre_cooccurrence([g["name"] for g in genres])

        # Add edges for strongly related genres
        for (genre1, genre2), strength in genre_cooccurrence.items():
            if strength > 0.1:  # Threshold for relationship strength
                self._add_edge(genre1, genre2, "related", weight=strength)

    def _calculate_genre_cooccurrence(self, genre_names: List[str]) -> Dict[Tuple[str, str], float]:
        """Calculate how often genres co-occur in user listening"""
        # Placeholder - would analyze user listening patterns
        # TODO: Implement actual co-occurrence calculation
        return {}

    def save_genre_hierarchy(self, genres: List[Dict]):
        """
        Save genre hierarchy to database

        Args:
            genres: List of genre dictionaries with hierarchy info
        """
        query = """
            INSERT INTO musicmatch.genre_hierarchy
                (genre_name, parent_genre, level, popularity_score, last_updated)
            VALUES
                (:genre_name, :parent_genre, :level, :popularity_score, NOW())
            ON CONFLICT (genre_name)
            DO UPDATE SET
                parent_genre = EXCLUDED.parent_genre,
                level = EXCLUDED.level,
                popularity_score = EXCLUDED.popularity_score,
                last_updated = NOW()
        """

        try:
            for genre in genres:
                db_conn.execute(
                    sqlalchemy.text(query),
                    {
                        "genre_name": genre["name"],
                        "parent_genre": genre.get("parent"),
                        "level": genre.get("level", 0),
                        "popularity_score": genre.get("popularity", 0.0)
                    }
                )

            db_conn.commit()
            current_app.logger.info(f"Saved {len(genres)} genres to hierarchy")
        except Exception as e:
            current_app.logger.error(f"Error saving genre hierarchy: {e}", exc_info=True)
            db_conn.rollback()


def build_genre_graph_from_tags(min_tag_count: int = 50) -> Dict:
    """
    Build a genre graph from MusicBrainz tags

    Args:
        min_tag_count: Minimum number of uses for a tag to be included

    Returns:
        Genre graph data
    """
    # TODO: Query MB tags and build genre graph
    # This would integrate with the tag_data tables
    graph = GenreGraph()
    return graph.generate_genre_landscape(min_popularity=min_tag_count)
