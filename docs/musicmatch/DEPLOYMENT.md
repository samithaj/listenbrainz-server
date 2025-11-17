# MusicMatch Deployment Guide

## Overview

This guide covers the deployment process for the MusicMatch feature extension to ListenBrainz Server. MusicMatch adds multi-service music integration, graph visualization, playlist synchronization, and unified playback capabilities.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Migration](#database-migration)
3. [OAuth Configuration](#oauth-configuration)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Verification](#verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **PostgreSQL/TimescaleDB**: 12 or higher
- **Node.js**: 16 or higher
- **Redis**: 5.0 or higher (for caching)

### External Service Accounts

Before deployment, register applications with each streaming service:

1. **Spotify**:
   - Register at: https://developer.spotify.com/dashboard
   - Required scopes: `user-read-playback-state`, `user-modify-playback-state`, `playlist-modify-public`, `playlist-modify-private`
   - Note Client ID and Client Secret

2. **Tidal**:
   - Register at: https://developer.tidal.com
   - Required scopes: Playlist management, Track search
   - Note Client ID and Client Secret

3. **YouTube Music** (via Google):
   - Register at: https://console.cloud.google.com
   - Enable YouTube Data API v3
   - Required scopes: `youtube`, `youtube.force-ssl`
   - Note Client ID and Client Secret

4. **Apple Music**:
   - Register at: https://developer.apple.com/musickit
   - Create MusicKit identifier
   - Generate developer token
   - Note Team ID, Key ID, and Private Key

---

## Database Migration

### 1. Backup Database

Before running any migrations, create a full database backup:

```bash
# PostgreSQL backup
pg_dump -h localhost -U listenbrainz listenbrainz > listenbrainz_backup_$(date +%Y%m%d).sql

# Or using TimescaleDB-specific backup
timescaledb-dump listenbrainz > listenbrainz_ts_backup_$(date +%Y%m%d).sql
```

### 2. Review Migration Scripts

Review the migration scripts in `admin/timescale/updates/`:

```bash
ls -la admin/timescale/updates/2025-11-17-add-musicmatch-*.sql
```

You should see:
- `2025-11-17-add-musicmatch-track-mapping.sql`
- `2025-11-17-add-musicmatch-graph-schema.sql`
- `2025-11-17-add-musicmatch-playlist-sync.sql`
- `2025-11-17-add-musicmatch-playback.sql`

### 3. Run Migrations

Execute migrations in order:

```bash
# Create musicmatch schema
psql -h localhost -U listenbrainz listenbrainz -f admin/timescale/updates/2025-11-17-add-musicmatch-track-mapping.sql

psql -h localhost -U listenbrainz listenbrainz -f admin/timescale/updates/2025-11-17-add-musicmatch-graph-schema.sql

psql -h localhost -U listenbrainz listenbrainz -f admin/timescale/updates/2025-11-17-add-musicmatch-playlist-sync.sql

psql -h localhost -U listenbrainz listenbrainz -f admin/timescale/updates/2025-11-17-add-musicmatch-playback.sql
```

### 4. Verify Migrations

```sql
-- Connect to database
psql -h localhost -U listenbrainz listenbrainz

-- Verify schema exists
\dn musicmatch

-- Verify tables
\dt musicmatch.*

-- Check table counts
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'musicmatch';
```

Expected tables:
- `track_service_mapping`
- `user_music_graph`
- `artist_relationships`
- `genre_hierarchy`
- `genre_relationships`
- `playlist_sync_mapping`
- `playlist_sync_settings`
- `playlist_sync_jobs`
- `playback_sessions`
- `playback_queue`
- `playback_history`

---

## OAuth Configuration

### 1. Update Configuration File

Add OAuth credentials to your ListenBrainz configuration file (usually `config.py` or environment variables):

```python
# Spotify
SPOTIFY_CLIENT_ID = "your-spotify-client-id"
SPOTIFY_CLIENT_SECRET = "your-spotify-client-secret"
SPOTIFY_REDIRECT_URI = "https://yourdomain.com/settings/music-services/spotify/callback"

# Tidal
TIDAL_CLIENT_ID = "your-tidal-client-id"
TIDAL_CLIENT_SECRET = "your-tidal-client-secret"
TIDAL_REDIRECT_URI = "https://yourdomain.com/settings/music-services/tidal/callback"

# YouTube Music (Google OAuth)
GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
YOUTUBE_MUSIC_REDIRECT_URI = "https://yourdomain.com/settings/music-services/youtube-music/callback"

# Apple Music
APPLE_TEAM_ID = "your-apple-team-id"
APPLE_KEY_ID = "your-apple-key-id"
APPLE_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
your-private-key-here
-----END PRIVATE KEY-----"""
```

### 2. Update OAuth Service Classes

Ensure the domain service classes reference the configuration:

```python
# In listenbrainz/domain/tidal.py
self.client_id = current_app.config.get('TIDAL_CLIENT_ID')
self.client_secret = current_app.config.get('TIDAL_CLIENT_SECRET')
```

### 3. Configure Callback URLs

In each service's developer console, configure the callback URLs:

- Spotify: `https://yourdomain.com/settings/music-services/spotify/callback`
- Tidal: `https://yourdomain.com/settings/music-services/tidal/callback`
- YouTube Music: `https://yourdomain.com/settings/music-services/youtube-music/callback`
- Apple Music: `https://yourdomain.com` (with additional MusicKit setup)

---

## Backend Deployment

### 1. Install Python Dependencies

If any new dependencies were added:

```bash
pip install -r requirements.txt
```

### 2. Run Tests

```bash
# Run backend tests
python -m pytest listenbrainz/background/playback/test_playback_router.py
python -m pytest listenbrainz/background/playlist_sync/test_sync_manager.py

# Run all tests
python -m pytest
```

### 3. Deploy Backend Code

```bash
# Pull latest code
git pull origin main

# Restart application servers
sudo systemctl restart listenbrainz-uwsgi
# Or
sudo systemctl restart listenbrainz-gunicorn
```

### 4. Verify API Endpoints

```bash
# Check API is responding
curl https://yourdomain.com/1/musicmatch/playback/stats

# Should return 401 if not authenticated
# If returns 404, routes aren't registered correctly
```

---

## Frontend Deployment

### 1. Install Node Dependencies

```bash
cd frontend/js
npm install
```

### 2. Run Frontend Tests

```bash
# Run component tests
npm test

# Run with coverage
npm test -- --coverage
```

### 3. Build Frontend

```bash
# Production build
npm run build

# Or development build
npm run build:dev
```

### 4. Deploy Static Assets

```bash
# Copy build artifacts to static directory
cp -r build/* /path/to/listenbrainz/static/

# If using CDN
aws s3 sync build/ s3://your-cdn-bucket/musicmatch/ --acl public-read
```

### 5. Clear CDN Cache

If using a CDN, clear the cache:

```bash
# CloudFlare
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'

# Or purge specific files
# --data '{"files":["https://yourdomain.com/static/musicmatch/main.js"]}'
```

---

## Verification

### 1. Smoke Tests

Perform basic smoke tests after deployment:

```bash
# Test homepage loads
curl -I https://yourdomain.com/

# Test MusicMatch API endpoints
curl https://yourdomain.com/1/musicmatch/playback/stats

# Test static assets
curl -I https://yourdomain.com/static/musicmatch/main.js
```

### 2. Feature Testing

1. **OAuth Connection**:
   - Navigate to Settings > Music Services
   - Connect to Spotify/Tidal/YouTube Music/Apple Music
   - Verify OAuth flow completes successfully
   - Check tokens are stored in database

2. **Graph Visualization**:
   - Navigate to MusicMatch > Graph Explorer
   - Load user music graph
   - Verify graph renders
   - Test layout controls

3. **Playlist Sync**:
   - Navigate to MusicMatch > Playlists
   - Select a playlist
   - Trigger sync to connected service
   - Verify sync completes successfully

4. **Playback**:
   - Navigate to MusicMatch > Dashboard
   - Play a track
   - Verify playback controls work (if using Spotify)

### 3. Database Verification

```sql
-- Check for data in new tables
SELECT COUNT(*) FROM musicmatch.track_service_mapping;
SELECT COUNT(*) FROM musicmatch.playback_sessions;
SELECT COUNT(*) FROM musicmatch.playlist_sync_mapping;

-- Check for recent activity
SELECT * FROM musicmatch.playback_history
ORDER BY played_at DESC
LIMIT 10;
```

### 4. Log Monitoring

Monitor logs for errors:

```bash
# Application logs
tail -f /var/log/listenbrainz/application.log | grep -i error

# UWSGI logs
tail -f /var/log/uwsgi/listenbrainz.log

# PostgreSQL logs
tail -f /var/log/postgresql/postgresql-12-main.log
```

---

## Rollback Procedures

### If Migration Fails

```bash
# Restore from backup
psql -h localhost -U listenbrainz listenbrainz < listenbrainz_backup_YYYYMMDD.sql

# Or drop musicmatch schema and retry
psql -h localhost -U listenbrainz listenbrainz -c "DROP SCHEMA IF EXISTS musicmatch CASCADE;"
```

### If Backend Deployment Fails

```bash
# Revert to previous version
git checkout <previous-commit>

# Restart services
sudo systemctl restart listenbrainz-uwsgi
```

### If Frontend Deployment Fails

```bash
# Revert static assets
git checkout <previous-commit> frontend/js/build/

# Or restore from backup
cp -r /backup/static/musicmatch/* /path/to/listenbrainz/static/musicmatch/

# Clear CDN cache
```

---

## Troubleshooting

### Database Issues

**Issue**: Migration fails with "schema already exists"
```sql
-- Drop and recreate
DROP SCHEMA IF EXISTS musicmatch CASCADE;
-- Then re-run migrations
```

**Issue**: Foreign key constraint errors
```sql
-- Check user table exists
SELECT COUNT(*) FROM "user";

-- Verify external_service_oauth table
SELECT * FROM external_service_oauth LIMIT 5;
```

### OAuth Issues

**Issue**: "OAuth callback not registered"
- Verify callback URL in service developer console
- Check configuration file has correct redirect URIs
- Ensure domain matches exactly (http vs https)

**Issue**: "Token refresh fails"
- Check refresh token exists in database
- Verify service credentials are correct
- Check service API status (may be down)

### API Issues

**Issue**: 404 errors on API endpoints
- Verify blueprints are registered in `listenbrainz/webserver/__init__.py`
- Check route prefixes are correct
- Restart application server

**Issue**: 500 errors on API calls
- Check application logs for stack traces
- Verify database connection
- Check all required configurations are set

### Frontend Issues

**Issue**: JavaScript errors in console
- Check build completed successfully
- Verify all dependencies installed
- Check for TypeScript compilation errors

**Issue**: Components not rendering
- Verify React version compatibility
- Check for missing imports
- Verify API endpoints are accessible

---

## Performance Optimization

### Database Indexing

Ensure all indexes are created:

```sql
-- Verify indexes exist
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'musicmatch';
```

### Caching

Configure Redis caching for frequently accessed data:

```python
# In config.py
REDIS_HOST = "localhost"
REDIS_PORT = 6379
CACHE_TTL = 3600  # 1 hour

# Cache graph data
# Cache track mappings
# Cache playback states
```

### Query Optimization

Monitor slow queries:

```sql
-- Enable slow query logging
ALTER DATABASE listenbrainz SET log_min_duration_statement = 1000;

-- Check slow queries
SELECT * FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

---

## Monitoring

### Metrics to Monitor

1. **API Response Times**:
   - Graph endpoints: < 2 seconds
   - Playlist sync: < 5 seconds
   - Playback control: < 500ms

2. **Database Performance**:
   - Connection pool usage
   - Query execution times
   - Lock wait times

3. **Service Health**:
   - OAuth token refresh success rate
   - External API call success rate
   - Sync job completion rate

### Alerting

Set up alerts for:
- High error rates (> 5%)
- Slow API responses (> 5 seconds p95)
- Failed sync jobs
- Database connection pool exhaustion

---

## Security Considerations

1. **OAuth Tokens**: Encrypt at rest in database
2. **API Keys**: Store in environment variables, never commit
3. **Rate Limiting**: Configure per-user limits
4. **Input Validation**: Sanitize all user inputs
5. **CORS**: Configure appropriate CORS headers
6. **HTTPS**: Enforce HTTPS for all OAuth callbacks

---

## Post-Deployment Checklist

- [ ] Database migrations completed successfully
- [ ] All OAuth services configured and tested
- [ ] Backend API endpoints responding correctly
- [ ] Frontend static assets deployed and accessible
- [ ] CDN cache cleared (if applicable)
- [ ] Smoke tests passed
- [ ] Feature tests passed
- [ ] Logs show no errors
- [ ] Monitoring dashboards updated
- [ ] Documentation updated
- [ ] Stakeholders notified

---

## Support

For deployment issues:
1. Check this guide first
2. Review application logs
3. Check GitHub issues
4. Contact ListenBrainz team on IRC/Discord

## Changelog

- **2025-11-17**: Initial deployment guide for MusicMatch v1.0
