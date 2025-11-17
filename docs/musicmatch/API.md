# MusicMatch API Documentation

## Overview

The MusicMatch API provides endpoints for multi-service music integration, graph visualization, playlist synchronization, and unified playback. All endpoints require authentication unless otherwise specified.

**Base URL**: `/1/musicmatch/`

**Authentication**: Required for all endpoints (Flask-Login session)

**Rate Limiting**: Applied to all endpoints (default: 100 requests/minute)

---

## Track Resolution API

### Get Track Services

Get available streaming services for a MusicBrainz recording.

```
GET /1/musicmatch/track/<recording_mbid>/services
```

**Parameters**:
- `recording_mbid` (path, required): MusicBrainz recording UUID

**Response** (`200 OK`):
```json
{
  "spotify": "spotify_track_id",
  "tidal": "tidal_track_id",
  "youtube_music": "youtube_video_id",
  "apple": "apple_song_id"
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/1/musicmatch/track/5b11f4ce-a62d-471e-81fc-a69a8278c7da/services
```

---

### Resolve Track

Resolve a track across multiple services using fuzzy matching.

```
POST /1/musicmatch/track/resolve
```

**Request Body**:
```json
{
  "track_name": "Bohemian Rhapsody",
  "artist_name": "Queen",
  "services": ["spotify", "tidal", "youtube_music"]
}
```

**Response** (`200 OK`):
```json
{
  "matches": {
    "spotify": {
      "track_id": "3z8h0TU7RN3qoQq0uFH8gX",
      "confidence": 0.98
    },
    "tidal": {
      "track_id": "25005918",
      "confidence": 0.95
    }
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/1/musicmatch/track/resolve \
  -H "Content-Type: application/json" \
  -d '{"track_name":"Bohemian Rhapsody","artist_name":"Queen","services":["spotify"]}'
```

---

## Graph API

### Get User Music Graph

Get user's personalized music graph based on listening history.

```
GET /1/musicmatch/graph/user/<user_name>
```

**Parameters**:
- `user_name` (path, required): ListenBrainz username
- `time_range` (query, optional): Time range for data (`week`, `month`, `year`, `all_time`). Default: `month`
- `graph_type` (query, optional): Type of graph (`artist`, `track`, `genre`, `combined`). Default: `combined`
- `max_artists` (query, optional): Maximum artists to include. Default: `50`
- `max_tracks` (query, optional): Maximum tracks to include. Default: `100`

**Response** (`200 OK`):
```json
{
  "graph": {
    "nodes": [
      {
        "id": "artist_123",
        "type": "artist",
        "label": "Queen",
        "weight": 100,
        "x": 250.5,
        "y": 300.2
      },
      {
        "id": "track_456",
        "type": "track",
        "label": "Bohemian Rhapsody",
        "weight": 50,
        "x": 280.1,
        "y": 320.5
      }
    ],
    "edges": [
      {
        "source": "artist_123",
        "target": "track_456",
        "type": "performed",
        "weight": 1.0
      }
    ]
  },
  "metadata": {
    "time_range": "month",
    "generated_at": "2025-11-17T10:00:00Z",
    "node_count": 75,
    "edge_count": 120
  }
}
```

**Example**:
```bash
curl http://localhost:8000/1/musicmatch/graph/user/johndoe?time_range=month
```

---

### Get Artist Relations Graph

Get relationship graph for a specific artist.

```
GET /1/musicmatch/graph/artist/<artist_mbid>
```

**Parameters**:
- `artist_mbid` (path, required): MusicBrainz artist UUID
- `depth` (query, optional): Relationship depth (1-3). Default: `2`
- `max_related` (query, optional): Maximum related artists. Default: `20`

**Response** (`200 OK`):
```json
{
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "metadata": {
    "artist_mbid": "5b11f4ce-a62d-471e-81fc-a69a8278c7da",
    "artist_name": "Queen",
    "depth": 2
  }
}
```

**Example**:
```bash
curl http://localhost:8000/1/musicmatch/graph/artist/5b11f4ce-a62d-471e-81fc-a69a8278c7da?depth=2
```

---

### Get Genre Graph

Get genre hierarchy or landscape graph.

```
GET /1/musicmatch/graph/genre
```

**Parameters**:
- `genre` (query, optional): Specific genre name. If not provided, returns full hierarchy.
- `type` (query, optional): Graph type (`hierarchy`, `landscape`). Default: `hierarchy`

**Response** (`200 OK`):
```json
{
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "metadata": {
    "genre": "rock",
    "type": "hierarchy"
  }
}
```

---

## Playlist Sync API

### Trigger Playlist Sync

Synchronize a playlist to one or more streaming services.

```
POST /1/musicmatch/playlist/<playlist_id>/sync
```

**Parameters**:
- `playlist_id` (path, required): ListenBrainz playlist UUID

**Request Body**:
```json
{
  "services": ["spotify", "tidal"],
  "force": false
}
```

**Response** (`200 OK`):
```json
{
  "job": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "lb_playlist_id": "playlist-uuid",
    "services": ["spotify", "tidal"],
    "status": "pending",
    "created_at": "2025-11-17T10:00:00Z"
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/1/musicmatch/playlist/abc123/sync \
  -H "Content-Type: application/json" \
  -d '{"services":["spotify","tidal"],"force":false}'
```

---

### Get Playlist Sync Status

Get current sync status for a playlist across all services.

```
GET /1/musicmatch/playlist/<playlist_id>/sync-status
```

**Parameters**:
- `playlist_id` (path, required): ListenBrainz playlist UUID

**Response** (`200 OK`):
```json
{
  "mappings": [
    {
      "service": "spotify",
      "external_playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
      "last_synced": "2025-11-17T10:00:00Z",
      "sync_status": "completed",
      "error_message": null
    },
    {
      "service": "tidal",
      "external_playlist_id": "01234567-89ab-cdef-0123-456789abcdef",
      "last_synced": null,
      "sync_status": "pending",
      "error_message": null
    }
  ]
}
```

---

### Get/Update Playlist Sync Settings

Get or update auto-sync settings for a playlist.

```
GET /1/musicmatch/playlist/<playlist_id>/sync-settings
POST /1/musicmatch/playlist/<playlist_id>/sync-settings
```

**Request Body** (POST only):
```json
{
  "auto_sync_enabled": true,
  "sync_services": ["spotify", "tidal"],
  "sync_frequency_minutes": 60
}
```

**Response** (`200 OK`):
```json
{
  "settings": {
    "auto_sync_enabled": true,
    "sync_services": ["spotify", "tidal"],
    "sync_frequency_minutes": 60,
    "created_at": "2025-11-17T09:00:00Z",
    "updated_at": "2025-11-17T10:00:00Z"
  }
}
```

---

### Get Sync Job Status

Get status of a specific sync job.

```
GET /1/musicmatch/playlist/jobs/<job_id>
```

**Parameters**:
- `job_id` (path, required): Sync job UUID

**Response** (`200 OK`):
```json
{
  "job": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "lb_playlist_id": "playlist-uuid",
    "services": ["spotify", "tidal"],
    "status": "completed",
    "started_at": "2025-11-17T10:00:00Z",
    "completed_at": "2025-11-17T10:01:30Z",
    "success_count": 2,
    "failure_count": 0,
    "error_message": null
  }
}
```

---

## Playback API

### Start Playback

Start playback of a track on the best available service.

```
POST /1/musicmatch/playback/play
```

**Request Body**:
```json
{
  "recording_mbid": "5b11f4ce-a62d-471e-81fc-a69a8278c7da",
  "preferred_service": "spotify"
}
```

**Response** (`200 OK`):
```json
{
  "success": true,
  "session_id": "session-uuid",
  "service": "spotify",
  "external_track_id": "3z8h0TU7RN3qoQq0uFH8gX",
  "supports_server_control": true
}
```

---

### Pause Playback

Pause current playback.

```
POST /1/musicmatch/playback/pause
```

**Response** (`200 OK`):
```json
{
  "success": true
}
```

---

### Resume Playback

Resume paused playback.

```
POST /1/musicmatch/playback/resume
```

**Response** (`200 OK`):
```json
{
  "success": true
}
```

---

### Skip Track

Skip to next track in queue.

```
POST /1/musicmatch/playback/skip
```

**Response** (`200 OK`):
```json
{
  "success": true
}
```

---

### Get Playback Status

Get current playback status and session information.

```
GET /1/musicmatch/playback/status
```

**Response** (`200 OK`):
```json
{
  "session": {
    "session_id": "session-uuid",
    "service": "spotify",
    "started_at": "2025-11-17T10:00:00Z"
  },
  "playback_state": {
    "is_playing": true,
    "progress_ms": 45000,
    "track_id": "3z8h0TU7RN3qoQq0uFH8gX",
    "track_name": "Bohemian Rhapsody",
    "artist_name": "Queen",
    "duration_ms": 354000,
    "device_name": "Desktop",
    "volume_percent": 75
  },
  "queue": [
    {
      "position": 0,
      "recording_mbid": "mbid-1",
      "added_at": "2025-11-17T10:00:00Z",
      "played_at": null
    }
  ],
  "supports_server_control": true
}
```

---

### Add to Queue

Add tracks to playback queue.

```
POST /1/musicmatch/playback/queue
```

**Request Body**:
```json
{
  "recording_mbids": [
    "5b11f4ce-a62d-471e-81fc-a69a8278c7da",
    "another-mbid-here"
  ]
}
```

**Response** (`200 OK`):
```json
{
  "success": true,
  "session_id": "session-uuid",
  "tracks_added": 2
}
```

---

### Get Queue

Get current playback queue.

```
GET /1/musicmatch/playback/queue
```

**Response** (`200 OK`):
```json
{
  "queue": [
    {
      "position": 0,
      "recording_mbid": "mbid-1",
      "added_at": "2025-11-17T10:00:00Z",
      "played_at": null
    },
    {
      "position": 1,
      "recording_mbid": "mbid-2",
      "added_at": "2025-11-17T10:01:00Z",
      "played_at": null
    }
  ]
}
```

---

### Get Playback History

Get user's playback history.

```
GET /1/musicmatch/playback/history?limit=50&offset=0
```

**Parameters**:
- `limit` (query, optional): Maximum results. Default: `50`, Max: `100`
- `offset` (query, optional): Results to skip. Default: `0`

**Response** (`200 OK`):
```json
{
  "history": [
    {
      "recording_mbid": "mbid-1",
      "service": "spotify",
      "played_at": "2025-11-17T10:00:00Z",
      "duration_ms": 180000,
      "session_id": "session-uuid"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

---

### Get Playback Statistics

Get playback statistics for the authenticated user.

```
GET /1/musicmatch/playback/stats
```

**Response** (`200 OK`):
```json
{
  "stats": {
    "total_plays": 1523,
    "unique_tracks": 456,
    "services_used": 3,
    "total_duration_ms": 9876543210
  }
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Rate Limiting

All API endpoints are rate limited to prevent abuse:

- **Default Limit**: 100 requests per minute
- **Burst Limit**: 200 requests per minute (short bursts)
- **Rate Limit Headers**:
  - `X-RateLimit-Limit`: Requests allowed per period
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Service-Specific Notes

### Spotify
- Requires active Spotify device for playback control
- Supports full server-side playback control
- Maximum 100 tracks per playlist add operation

### Tidal
- Requires Tidal client app for playback
- Limited server-side API support
- Track resolution available via API

### YouTube Music
- Requires client-side iframe player
- No server-side playback control
- Video info retrieval available

### Apple Music
- Requires MusicKit JS for playback
- No server-side playback control
- Catalog search available via API

---

## Best Practices

1. **Caching**: Cache graph and track mapping data to reduce API calls
2. **Batch Operations**: Use batch endpoints when adding multiple tracks
3. **Error Handling**: Always handle error responses gracefully
4. **Rate Limiting**: Implement exponential backoff for rate limit errors
5. **Service Availability**: Check service connection status before operations
6. **Polling**: Use reasonable intervals (5+ seconds) when polling for status

---

## Examples

### Complete Workflow: Sync Playlist

```bash
# 1. Get playlist sync settings
curl http://localhost:8000/1/musicmatch/playlist/abc123/sync-settings

# 2. Trigger sync to Spotify and Tidal
curl -X POST http://localhost:8000/1/musicmatch/playlist/abc123/sync \
  -H "Content-Type: application/json" \
  -d '{"services":["spotify","tidal"],"force":false}'

# Response: {"job":{"job_id":"job-123",...}}

# 3. Poll job status
curl http://localhost:8000/1/musicmatch/playlist/jobs/job-123

# 4. Check final sync status
curl http://localhost:8000/1/musicmatch/playlist/abc123/sync-status
```

### Complete Workflow: Play Track

```bash
# 1. Find track on services
curl http://localhost:8000/1/musicmatch/track/mbid-123/services

# 2. Start playback
curl -X POST http://localhost:8000/1/musicmatch/playback/play \
  -H "Content-Type: application/json" \
  -d '{"recording_mbid":"mbid-123","preferred_service":"spotify"}'

# 3. Check playback status
curl http://localhost:8000/1/musicmatch/playback/status

# 4. Pause playback
curl -X POST http://localhost:8000/1/musicmatch/playback/pause
```

---

## Changelog

### Version 1.0 (2025-11-17)
- Initial MusicMatch API release
- Track resolution endpoints
- Graph visualization endpoints
- Playlist sync endpoints
- Unified playback endpoints
