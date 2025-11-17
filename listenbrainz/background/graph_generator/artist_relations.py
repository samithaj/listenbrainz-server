"""
Artist Relations Graph Generator

Generates graphs showing relationships between artists including:
- Collaborations
- Band memberships
- Similar artists
- Shared genres
"""

import json
from typing import Dict, List, Optional, Set
import sqlalchemy
from flask import current_app

from listenbrainz.webserver import db_conn


class ArtistRelationsGraph:
    """Generates relationship graphs for artists"""

    def __init__(self, artist_mbid: str):
        self.artist_mbid = artist_mbid
        self.graph_data = {
            "nodes": [],
            "edges": [],
            "metadata": {}
        }
        self.processed_artists: Set[str] = set()

    def generate_graph(self, depth: int = 2, max_related: int = 20) -> Dict:
        """
        Generate artist relationship graph

        Args:
            depth: How many levels of relationships to explore (1-3)
            max_related: Maximum number of related artists per level

        Returns:
            Graph data with artist nodes and relationship edges
        """
        if depth < 1 or depth > 3:
            raise ValueError("Depth must be between 1 and 3")

        # Add root artist node
        root_artist = self._get_artist_info(self.artist_mbid)
        if not root_artist:
            raise ValueError(f"Artist {self.artist_mbid} not found")

        self._add_artist_node(root_artist, is_root=True)
        self.processed_artists.add(self.artist_mbid)

        # Recursively build graph
        self._build_relationships(self.artist_mbid, current_depth=1, max_depth=depth, max_related=max_related)

        # Add metadata
        self.graph_data["metadata"] = {
            "root_artist_mbid": self.artist_mbid,
            "root_artist_name": root_artist.get("name", "Unknown"),
            "depth": depth,
            "node_count": len(self.graph_data["nodes"]),
            "edge_count": len(self.graph_data["edges"])
        }

        return self.graph_data

    def _get_artist_info(self, artist_mbid: str) -> Optional[Dict]:
        """Get basic artist information"""
        # Placeholder - would query MusicBrainz or local cache
        # For now, return minimal info
        return {
            "mbid": artist_mbid,
            "name": f"Artist {artist_mbid[:8]}"  # Temporary
        }

    def _add_artist_node(self, artist: Dict, is_root: bool = False):
        """Add an artist node to the graph"""
        node = {
            "id": f"artist_{artist['mbid']}",
            "type": "artist",
            "label": artist.get("name", "Unknown Artist"),
            "mbid": artist["mbid"],
            "is_root": is_root,
            "metadata": artist
        }
        self.graph_data["nodes"].append(node)

    def _build_relationships(
        self,
        artist_mbid: str,
        current_depth: int,
        max_depth: int,
        max_related: int
    ):
        """Recursively build artist relationships"""
        if current_depth > max_depth:
            return

        # Get different types of relationships
        collaborators = self._get_collaborators(artist_mbid, limit=max_related)
        band_members = self._get_band_members(artist_mbid, limit=max_related)
        similar_artists = self._get_similar_artists(artist_mbid, limit=max_related)

        # Process collaborators
        for collab in collaborators:
            if collab["mbid"] not in self.processed_artists:
                artist_info = self._get_artist_info(collab["mbid"])
                if artist_info:
                    self._add_artist_node(artist_info)
                    self.processed_artists.add(collab["mbid"])

            # Add edge
            self._add_edge(
                artist_mbid,
                collab["mbid"],
                "collaboration",
                weight=collab.get("strength", 1.0)
            )

            # Recurse if not at max depth
            if current_depth < max_depth and collab["mbid"] not in self.processed_artists:
                self._build_relationships(
                    collab["mbid"],
                    current_depth + 1,
                    max_depth,
                    max_related // 2  # Reduce related count at deeper levels
                )

        # Process band members
        for member in band_members:
            if member["mbid"] not in self.processed_artists:
                artist_info = self._get_artist_info(member["mbid"])
                if artist_info:
                    self._add_artist_node(artist_info)
                    self.processed_artists.add(member["mbid"])

            self._add_edge(
                artist_mbid,
                member["mbid"],
                "member_of",
                weight=1.0
            )

        # Process similar artists
        for similar in similar_artists:
            if similar["mbid"] not in self.processed_artists:
                artist_info = self._get_artist_info(similar["mbid"])
                if artist_info:
                    self._add_artist_node(artist_info)
                    self.processed_artists.add(similar["mbid"])

            self._add_edge(
                artist_mbid,
                similar["mbid"],
                "similar",
                weight=similar.get("similarity", 0.5)
            )

    def _add_edge(self, source_mbid: str, target_mbid: str, edge_type: str, weight: float = 1.0):
        """Add an edge to the graph"""
        edge = {
            "source": f"artist_{source_mbid}",
            "target": f"artist_{target_mbid}",
            "type": edge_type,
            "weight": weight
        }
        self.graph_data["edges"].append(edge)

    def _get_collaborators(self, artist_mbid: str, limit: int = 20) -> List[Dict]:
        """Get artists who have collaborated with this artist"""
        # Query artist_credit_artist_mbid_similarity table
        query = """
            SELECT artist_mbid_1 as mbid,
                   score as strength
              FROM similarity.artist_credit_mbid
             WHERE artist_mbid_0 = :artist_mbid
          ORDER BY score DESC
             LIMIT :limit
        """

        try:
            result = db_conn.execute(
                sqlalchemy.text(query),
                {"artist_mbid": artist_mbid, "limit": limit}
            )
            return [{"mbid": str(row.mbid), "strength": float(row.strength)} for row in result]
        except Exception as e:
            current_app.logger.error(f"Error fetching collaborators: {e}")
            return []

    def _get_band_members(self, artist_mbid: str, limit: int = 20) -> List[Dict]:
        """Get band members or member bands for this artist"""
        # Placeholder - would query MusicBrainz relationships
        # TODO: Implement with actual MB relationship data
        return []

    def _get_similar_artists(self, artist_mbid: str, limit: int = 20) -> List[Dict]:
        """Get similar artists based on listening patterns"""
        # Query similarity tables
        query = """
            SELECT artist_mbid_1 as mbid,
                   score as similarity
              FROM similarity.artist
             WHERE artist_mbid_0 = :artist_mbid
          ORDER BY score DESC
             LIMIT :limit
        """

        try:
            result = db_conn.execute(
                sqlalchemy.text(query),
                {"artist_mbid": artist_mbid, "limit": limit}
            )
            return [{"mbid": str(row.mbid), "similarity": float(row.similarity)} for row in result]
        except Exception as e:
            current_app.logger.error(f"Error fetching similar artists: {e}")
            return []

    def save_to_database(self):
        """Save the artist relationship graph to database"""
        query = """
            INSERT INTO musicmatch.artist_relationships
                (artist_mbid_1, artist_mbid_2, relationship_type, strength, last_updated)
            VALUES
                (:artist_mbid_1, :artist_mbid_2, :relationship_type, :strength, NOW())
            ON CONFLICT (artist_mbid_1, artist_mbid_2, relationship_type)
            DO UPDATE SET
                strength = EXCLUDED.strength,
                last_updated = NOW()
        """

        try:
            # Save each edge as a relationship
            for edge in self.graph_data["edges"]:
                # Extract MBIDs from node IDs
                source_mbid = edge["source"].replace("artist_", "")
                target_mbid = edge["target"].replace("artist_", "")

                db_conn.execute(
                    sqlalchemy.text(query),
                    {
                        "artist_mbid_1": source_mbid,
                        "artist_mbid_2": target_mbid,
                        "relationship_type": edge["type"],
                        "strength": edge["weight"]
                    }
                )

            db_conn.commit()
            current_app.logger.info(
                f"Saved artist relationships for {self.artist_mbid}"
            )
        except Exception as e:
            current_app.logger.error(
                f"Error saving artist relationships: {e}",
                exc_info=True
            )
            db_conn.rollback()


def get_artist_relationship_graph(artist_mbid: str, depth: int = 2) -> Optional[Dict]:
    """
    Get or generate artist relationship graph

    Args:
        artist_mbid: Artist MBID
        depth: Relationship depth

    Returns:
        Graph data dictionary
    """
    try:
        generator = ArtistRelationsGraph(artist_mbid)
        return generator.generate_graph(depth=depth)
    except Exception as e:
        current_app.logger.error(f"Error generating artist graph: {e}")
        return None
