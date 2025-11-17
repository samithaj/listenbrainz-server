BEGIN;

-- Table for caching user music graphs
CREATE TABLE IF NOT EXISTS musicmatch.user_music_graph (
    user_id INTEGER NOT NULL,
    graph_type TEXT NOT NULL,  -- 'artist', 'track', 'genre', 'combined'
    time_range TEXT,  -- 'week', 'month', 'year', 'all_time'
    graph_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, graph_type, time_range),
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- Index for querying user graphs by generation time
CREATE INDEX IF NOT EXISTS idx_user_music_graph_generated
ON musicmatch.user_music_graph(user_id, generated_at DESC);

-- Table for storing artist relationships
CREATE TABLE IF NOT EXISTS musicmatch.artist_relationships (
    artist_mbid_1 UUID NOT NULL,
    artist_mbid_2 UUID NOT NULL,
    relationship_type TEXT NOT NULL,  -- 'collaboration', 'similar', 'member_of'
    strength REAL,  -- 0.0 to 1.0 relationship strength
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (artist_mbid_1, artist_mbid_2, relationship_type)
);

-- Indexes for artist relationships
CREATE INDEX IF NOT EXISTS idx_artist_rel_1
ON musicmatch.artist_relationships(artist_mbid_1, relationship_type);

CREATE INDEX IF NOT EXISTS idx_artist_rel_2
ON musicmatch.artist_relationships(artist_mbid_2, relationship_type);

CREATE INDEX IF NOT EXISTS idx_artist_rel_strength
ON musicmatch.artist_relationships(strength DESC)
WHERE strength IS NOT NULL;

-- Table for genre hierarchy and taxonomy
CREATE TABLE IF NOT EXISTS musicmatch.genre_hierarchy (
    genre_name TEXT PRIMARY KEY,
    parent_genre TEXT,
    level INTEGER DEFAULT 0,
    popularity_score REAL DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (parent_genre) REFERENCES musicmatch.genre_hierarchy(genre_name) ON DELETE SET NULL
);

-- Index for querying by parent genre
CREATE INDEX IF NOT EXISTS idx_genre_parent
ON musicmatch.genre_hierarchy(parent_genre);

-- Index for querying by popularity
CREATE INDEX IF NOT EXISTS idx_genre_popularity
ON musicmatch.genre_hierarchy(popularity_score DESC);

-- Index for querying by level
CREATE INDEX IF NOT EXISTS idx_genre_level
ON musicmatch.genre_hierarchy(level);

-- Table for genre-to-genre relationships (co-occurrence, similarity)
CREATE TABLE IF NOT EXISTS musicmatch.genre_relationships (
    genre_1 TEXT NOT NULL,
    genre_2 TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- 'related', 'similar', 'subgenre'
    strength REAL,  -- 0.0 to 1.0
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (genre_1, genre_2, relationship_type),
    FOREIGN KEY (genre_1) REFERENCES musicmatch.genre_hierarchy(genre_name) ON DELETE CASCADE,
    FOREIGN KEY (genre_2) REFERENCES musicmatch.genre_hierarchy(genre_name) ON DELETE CASCADE
);

-- Index for genre relationships
CREATE INDEX IF NOT EXISTS idx_genre_rel_1
ON musicmatch.genre_relationships(genre_1, relationship_type);

CREATE INDEX IF NOT EXISTS idx_genre_rel_2
ON musicmatch.genre_relationships(genre_2, relationship_type);

-- Add comments for documentation
COMMENT ON TABLE musicmatch.user_music_graph IS
'Cached user music graphs generated from listening history';

COMMENT ON COLUMN musicmatch.user_music_graph.user_id IS
'ListenBrainz user ID';

COMMENT ON COLUMN musicmatch.user_music_graph.graph_type IS
'Type of graph: artist, track, genre, or combined';

COMMENT ON COLUMN musicmatch.user_music_graph.time_range IS
'Time range for graph data: week, month, year, or all_time';

COMMENT ON COLUMN musicmatch.user_music_graph.graph_data IS
'Graph data in JSON format with nodes and edges';

COMMENT ON TABLE musicmatch.artist_relationships IS
'Relationships between artists (collaborations, similarities, band memberships)';

COMMENT ON COLUMN musicmatch.artist_relationships.relationship_type IS
'Type of relationship: collaboration, similar, member_of, etc.';

COMMENT ON COLUMN musicmatch.artist_relationships.strength IS
'Relationship strength score (0.0-1.0), higher means stronger relationship';

COMMENT ON TABLE musicmatch.genre_hierarchy IS
'Genre taxonomy and hierarchy with popularity scores';

COMMENT ON COLUMN musicmatch.genre_hierarchy.parent_genre IS
'Parent genre in the hierarchy (NULL for top-level genres)';

COMMENT ON COLUMN musicmatch.genre_hierarchy.level IS
'Level in the hierarchy (0 for top-level)';

COMMENT ON COLUMN musicmatch.genre_hierarchy.popularity_score IS
'Genre popularity score based on listening patterns';

COMMENT ON TABLE musicmatch.genre_relationships IS
'Relationships between genres (similarity, co-occurrence)';

COMMIT;
