BEGIN;

-- Table for tracking playback sessions
CREATE TABLE IF NOT EXISTS musicmatch.playback_sessions (
    session_id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    service VARCHAR NOT NULL,  -- Service used for playback
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- Index for querying user's sessions
CREATE INDEX IF NOT EXISTS idx_playback_sessions_user
ON musicmatch.playback_sessions(user_id, started_at DESC);

-- Index for finding active sessions
CREATE INDEX IF NOT EXISTS idx_playback_sessions_active
ON musicmatch.playback_sessions(user_id, session_id)
WHERE ended_at IS NULL;

-- Table for playback queue
CREATE TABLE IF NOT EXISTS musicmatch.playback_queue (
    session_id UUID NOT NULL,
    position INTEGER NOT NULL,
    recording_mbid UUID NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    played_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (session_id, position),
    FOREIGN KEY (session_id) REFERENCES musicmatch.playback_sessions(session_id) ON DELETE CASCADE
);

-- Index for querying queue by session
CREATE INDEX IF NOT EXISTS idx_playback_queue_session
ON musicmatch.playback_queue(session_id, position);

-- Index for finding unplayed tracks
CREATE INDEX IF NOT EXISTS idx_playback_queue_unplayed
ON musicmatch.playback_queue(session_id, position)
WHERE played_at IS NULL;

-- Table for playback history (similar to listens but for MusicMatch playback)
CREATE TABLE IF NOT EXISTS musicmatch.playback_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    recording_mbid UUID NOT NULL,
    service VARCHAR NOT NULL,
    played_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_ms INTEGER,  -- How long the track was played
    session_id UUID,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES musicmatch.playback_sessions(session_id) ON DELETE SET NULL
);

-- Index for querying user's playback history
CREATE INDEX IF NOT EXISTS idx_playback_history_user
ON musicmatch.playback_history(user_id, played_at DESC);

-- Index for querying by service
CREATE INDEX IF NOT EXISTS idx_playback_history_service
ON musicmatch.playback_history(service, played_at DESC);

-- Index for querying by track
CREATE INDEX IF NOT EXISTS idx_playback_history_track
ON musicmatch.playback_history(recording_mbid, played_at DESC);

-- Add comments for documentation
COMMENT ON TABLE musicmatch.playback_sessions IS
'Tracks playback sessions for unified multi-service playback';

COMMENT ON COLUMN musicmatch.playback_sessions.session_id IS
'Unique session identifier';

COMMENT ON COLUMN musicmatch.playback_sessions.service IS
'External service used for this playback session (spotify, tidal, youtube_music, apple)';

COMMENT ON TABLE musicmatch.playback_queue IS
'Queue of tracks for playback in a session';

COMMENT ON COLUMN musicmatch.playback_queue.position IS
'Position in the queue (0-indexed)';

COMMENT ON COLUMN musicmatch.playback_queue.played_at IS
'Timestamp when track was played (NULL if not yet played)';

COMMENT ON TABLE musicmatch.playback_history IS
'Historical record of tracks played through MusicMatch';

COMMENT ON COLUMN musicmatch.playback_history.duration_ms IS
'How long the track was played in milliseconds';

COMMIT;
