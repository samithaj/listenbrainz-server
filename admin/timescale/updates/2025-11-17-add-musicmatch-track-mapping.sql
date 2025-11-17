BEGIN;

-- Create musicmatch schema for MusicMatch extension
CREATE SCHEMA IF NOT EXISTS musicmatch;

-- Create custom type for external service OAuth types if needed
-- Note: We'll use VARCHAR to match the external_service_oauth table's service column type

-- Table for storing track mappings between MusicBrainz recordings and external services
CREATE TABLE IF NOT EXISTS musicmatch.track_service_mapping (
    recording_mbid UUID NOT NULL,
    service VARCHAR NOT NULL,  -- Matches external_service_oauth.service type
    external_track_id TEXT NOT NULL,
    confidence REAL,  -- 0.0 to 1.0 matching confidence
    last_verified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (recording_mbid, service)
);

-- Create index for querying by service and external track ID
CREATE INDEX IF NOT EXISTS idx_track_mapping_service
ON musicmatch.track_service_mapping(service, external_track_id);

-- Create index for querying by recording_mbid
CREATE INDEX IF NOT EXISTS idx_track_mapping_mbid
ON musicmatch.track_service_mapping(recording_mbid);

-- Create index for querying by confidence (for quality filtering)
CREATE INDEX IF NOT EXISTS idx_track_mapping_confidence
ON musicmatch.track_service_mapping(confidence DESC)
WHERE confidence IS NOT NULL;

-- Add comment on table
COMMENT ON TABLE musicmatch.track_service_mapping IS
'Maps MusicBrainz recording MBIDs to external music service track IDs (Spotify, Tidal, YouTube Music, etc.)';

COMMENT ON COLUMN musicmatch.track_service_mapping.recording_mbid IS
'MusicBrainz Recording MBID';

COMMENT ON COLUMN musicmatch.track_service_mapping.service IS
'External service name (spotify, tidal, youtube_music, apple, etc.)';

COMMENT ON COLUMN musicmatch.track_service_mapping.external_track_id IS
'Track/song ID in the external service';

COMMENT ON COLUMN musicmatch.track_service_mapping.confidence IS
'Matching confidence score (0.0-1.0), higher means more confident match';

COMMENT ON COLUMN musicmatch.track_service_mapping.last_verified IS
'Timestamp when this mapping was last verified or updated';

COMMIT;
