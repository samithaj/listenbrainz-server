BEGIN;

-- Table for mapping ListenBrainz playlists to external service playlists
CREATE TABLE IF NOT EXISTS musicmatch.playlist_sync_mapping (
    lb_playlist_id UUID NOT NULL,
    service VARCHAR NOT NULL,  -- Matches external_service_oauth.service type
    external_playlist_id TEXT NOT NULL,
    last_synced TIMESTAMP WITH TIME ZONE,
    sync_status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    error_message TEXT,
    PRIMARY KEY (lb_playlist_id, service)
);

-- Index for querying by external playlist ID
CREATE INDEX IF NOT EXISTS idx_playlist_sync_external
ON musicmatch.playlist_sync_mapping(service, external_playlist_id);

-- Index for querying by status
CREATE INDEX IF NOT EXISTS idx_playlist_sync_status
ON musicmatch.playlist_sync_mapping(sync_status)
WHERE sync_status IN ('pending', 'in_progress', 'failed');

-- Index for querying by last synced time
CREATE INDEX IF NOT EXISTS idx_playlist_sync_time
ON musicmatch.playlist_sync_mapping(last_synced DESC NULLS LAST);

-- Table for playlist sync settings
CREATE TABLE IF NOT EXISTS musicmatch.playlist_sync_settings (
    lb_playlist_id UUID PRIMARY KEY,
    auto_sync_enabled BOOLEAN DEFAULT TRUE,
    sync_services TEXT[],  -- Array of service names to sync with
    sync_frequency_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for finding playlists that need auto-sync
CREATE INDEX IF NOT EXISTS idx_playlist_autosync
ON musicmatch.playlist_sync_settings(lb_playlist_id)
WHERE auto_sync_enabled = true;

-- Table for tracking sync jobs
CREATE TABLE IF NOT EXISTS musicmatch.playlist_sync_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lb_playlist_id UUID NOT NULL,
    services TEXT[] NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for querying jobs by playlist
CREATE INDEX IF NOT EXISTS idx_sync_jobs_playlist
ON musicmatch.playlist_sync_jobs(lb_playlist_id, created_at DESC);

-- Index for querying running jobs
CREATE INDEX IF NOT EXISTS idx_sync_jobs_status
ON musicmatch.playlist_sync_jobs(status)
WHERE status IN ('pending', 'running');

-- Add comments for documentation
COMMENT ON TABLE musicmatch.playlist_sync_mapping IS
'Maps ListenBrainz playlists to external service playlists for synchronization';

COMMENT ON COLUMN musicmatch.playlist_sync_mapping.lb_playlist_id IS
'ListenBrainz playlist UUID';

COMMENT ON COLUMN musicmatch.playlist_sync_mapping.service IS
'External service name (spotify, tidal, youtube_music, apple)';

COMMENT ON COLUMN musicmatch.playlist_sync_mapping.external_playlist_id IS
'Playlist ID in the external service';

COMMENT ON COLUMN musicmatch.playlist_sync_mapping.sync_status IS
'Current sync status: pending, in_progress, completed, failed';

COMMENT ON TABLE musicmatch.playlist_sync_settings IS
'Sync settings and preferences for each playlist';

COMMENT ON COLUMN musicmatch.playlist_sync_settings.auto_sync_enabled IS
'Whether automatic synchronization is enabled';

COMMENT ON COLUMN musicmatch.playlist_sync_settings.sync_services IS
'Array of service names to automatically sync with';

COMMENT ON COLUMN musicmatch.playlist_sync_settings.sync_frequency_minutes IS
'How often to sync automatically (in minutes)';

COMMENT ON TABLE musicmatch.playlist_sync_jobs IS
'Tracks sync job executions for monitoring and debugging';

COMMENT ON COLUMN musicmatch.playlist_sync_jobs.job_id IS
'Unique job identifier';

COMMENT ON COLUMN musicmatch.playlist_sync_jobs.status IS
'Job status: pending, running, completed, failed';

COMMIT;
