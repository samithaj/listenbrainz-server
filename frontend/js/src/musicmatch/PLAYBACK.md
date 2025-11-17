# Unified Playback System

## Overview

The Unified Playback System enables seamless music playback across multiple streaming services (Spotify, Tidal, YouTube Music, and Apple Music). The system automatically selects the best available service for each track and provides a unified interface for playback control.

## Architecture

### Backend Components

**Playback Router** (`listenbrainz/background/playback/playback_router.py`):
- Orchestrates playback across services
- Selects optimal service based on availability and preferences
- Manages playback sessions and queues
- Tracks playback state

**Service Players**:
- `SpotifyPlayer` - Full playback control via Spotify Web API
- `TidalPlayer` - Limited API support, requires client SDK
- `YoutubeMusicPlayer` - Requires client-side iframe player
- `AppleMusicPlayer` - Requires client-side MusicKit JS

**Database Schema**:
- `playback_sessions` - Active and historical playback sessions
- `playback_queue` - Tracks queued for playback
- `playback_history` - Historical playback data

### API Endpoints

All endpoints are under `/1/musicmatch/playback/`:

**POST /play**
```json
{
  "recording_mbid": "uuid",
  "preferred_service": "spotify"  // optional
}
```
Starts playback of a track on the best available service.

**POST /pause**
Pauses current playback (Spotify only).

**POST /resume**
Resumes paused playback (Spotify only).

**POST /skip**
Skips to the next track in the queue (Spotify only).

**GET /status**
```json
{
  "session": {
    "session_id": "uuid",
    "service": "spotify",
    "started_at": "2025-11-17T10:00:00Z"
  },
  "playback_state": {
    "is_playing": true,
    "progress_ms": 45000,
    "track_id": "...",
    "track_name": "Song Title",
    "artist_name": "Artist Name",
    "duration_ms": 180000
  },
  "queue": [...],
  "supports_server_control": true
}
```
Returns current playback status.

**POST /queue**
```json
{
  "recording_mbids": ["uuid1", "uuid2", ...]
}
```
Adds tracks to the playback queue.

**GET /queue**
Returns the current playback queue.

**GET /history**
Query params: `limit`, `offset`
Returns user's playback history.

**GET /stats**
Returns playback statistics (total plays, unique tracks, etc.).

## Service Capabilities

### Spotify
- **Server Control**: ✅ Yes
- **Playback Control**: Full (play, pause, resume, skip, seek, volume)
- **Queue Management**: ✅ Yes
- **State Reporting**: ✅ Yes
- **Requirements**: Active Spotify device

### Tidal
- **Server Control**: ❌ No
- **Playback Control**: Requires client SDK
- **Queue Management**: Via client SDK
- **State Reporting**: ❌ No
- **Requirements**: Tidal client app

### YouTube Music
- **Server Control**: ❌ No
- **Playback Control**: Requires iframe player
- **Queue Management**: Via client SDK
- **State Reporting**: ❌ No
- **Requirements**: YouTube iframe player

### Apple Music
- **Server Control**: ❌ No
- **Playback Control**: Requires MusicKit JS
- **Queue Management**: Via MusicKit JS
- **State Reporting**: ❌ No
- **Requirements**: MusicKit JS integration

## Frontend Integration

### UnifiedPlayer Component

The `UnifiedPlayer` component provides a unified playback interface:

```tsx
import { UnifiedPlayer } from "@/musicmatch/components";

function App() {
  return (
    <UnifiedPlayer
      onTrackChange={(mbid) => console.log("Playing:", mbid)}
    />
  );
}
```

**Features**:
- Automatic status polling (every 5 seconds)
- Service indicator showing current playback service
- Play/pause/skip controls (when supported)
- Progress bar with time display
- Queue information
- Error handling and user feedback

### Playing a Track

```tsx
import { UnifiedPlayer } from "@/musicmatch/components";

// Component will handle playback internally
<UnifiedPlayer />

// Or programmatically via API:
fetch("/1/musicmatch/playback/play", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    recording_mbid: "track-uuid",
    preferred_service: "spotify"  // optional
  })
});
```

## Service Selection Logic

The playback router selects services in this order:

1. **User Preference**: If user specifies a preferred service, use it
2. **Service Priority**:
   - Spotify (priority: 4)
   - Tidal (priority: 3)
   - Apple Music (priority: 2)
   - YouTube Music (priority: 1)
3. **Availability**: Service must have the track and user must be connected
4. **Fallback**: First available service if no preference matches

## Playback Sessions

Sessions track continuous playback activity:

```python
session = {
    "session_id": "uuid",
    "user_id": 123,
    "service": "spotify",
    "started_at": "2025-11-17T10:00:00Z",
    "ended_at": null  # null while active
}
```

Sessions end when:
- User explicitly stops playback
- User switches to a different service
- Session timeout (configurable)

## Queue Management

The playback queue maintains ordered tracks:

```python
queue_item = {
    "session_id": "uuid",
    "position": 0,
    "recording_mbid": "track-uuid",
    "added_at": "2025-11-17T10:00:00Z",
    "played_at": "2025-11-17T10:05:00Z"  # null if not played yet
}
```

**Operations**:
- Add tracks to queue
- Get current queue
- Mark tracks as played
- Clear queue (when session ends)

## Playback History

All playback is recorded for analytics:

```python
history_item = {
    "user_id": 123,
    "recording_mbid": "track-uuid",
    "service": "spotify",
    "played_at": "2025-11-17T10:00:00Z",
    "duration_ms": 180000,
    "session_id": "uuid"
}
```

This data powers:
- Listening statistics
- Service usage analytics
- Personalized recommendations
- User listening reports

## Client-Side Integration

For services requiring client-side control (Tidal, YouTube Music, Apple Music):

### YouTube Music

```html
<iframe
  id="youtube-player"
  src="https://www.youtube.com/embed/{VIDEO_ID}?enablejsapi=1"
  frameborder="0"
  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
></iframe>

<script>
  // Use YouTube iframe API
  var player = new YT.Player('youtube-player', {
    events: {
      'onReady': onPlayerReady,
      'onStateChange': onPlayerStateChange
    }
  });
</script>
```

### Apple Music

```html
<script src="https://js-cdn.music.apple.com/musickit/v3/musickit.js"></script>

<script>
  MusicKit.configure({
    developerToken: 'YOUR_DEVELOPER_TOKEN',
    app: {
      name: 'ListenBrainz',
      build: '1.0.0'
    }
  });

  const music = MusicKit.getInstance();
  await music.authorize();

  // Play track
  await music.setQueue({
    song: 'APPLE_MUSIC_TRACK_ID'
  });
  await music.play();
</script>
```

### Tidal

Tidal requires their proprietary SDK which is not publicly available. Users must use the Tidal desktop or mobile app for playback.

## Error Handling

Common errors and solutions:

### No Active Device (Spotify)
**Error**: "No active Spotify device found"
**Solution**: User must have Spotify app open on at least one device

### Token Expired
**Error**: "Failed to fetch playback status"
**Solution**: Token refresh handled automatically; user may need to re-authenticate

### Track Not Available
**Error**: "Track not available on any connected service"
**Solution**: Track not found in user's connected services; prompt to connect more services

### Service Requires Client SDK
**Info**: "Playback requires [service] client"
**Solution**: Direct user to open track in service's app

## Performance Considerations

1. **Status Polling**: Default 5-second interval, configurable
2. **Queue Management**: Batched operations where possible
3. **Session Cleanup**: Automatic cleanup of ended sessions
4. **History Retention**: Configurable retention period for playback history

## Future Enhancements

1. **Gapless Playback**: Seamless transitions between tracks
2. **Crossfade**: Fade between tracks (Spotify supports this)
3. **Equalizer**: Audio equalization settings
4. **Lyrics Integration**: Real-time lyrics display
5. **Collaborative Listening**: Shared playback sessions
6. **Smart Shuffling**: AI-powered shuffle based on listening patterns
7. **Offline Mode**: Download tracks for offline playback
8. **Audio Quality Selection**: Choose bitrate/quality per service

## Testing

### Manual Testing

1. Connect multiple services (Settings > Music Services)
2. Play a track available on multiple services
3. Verify correct service selection
4. Test playback controls (play/pause/skip)
5. Check queue management
6. Review playback history

### API Testing

```bash
# Start playback
curl -X POST http://localhost:8000/1/musicmatch/playback/play \
  -H "Content-Type: application/json" \
  -d '{"recording_mbid": "UUID"}'

# Get status
curl http://localhost:8000/1/musicmatch/playback/status

# Add to queue
curl -X POST http://localhost:8000/1/musicmatch/playback/queue \
  -H "Content-Type: application/json" \
  -d '{"recording_mbids": ["UUID1", "UUID2"]}'
```

## Troubleshooting

### Playback Won't Start
1. Check if user has connected services
2. Verify track is available on at least one service
3. Check OAuth tokens are valid
4. For Spotify: ensure device is active

### Controls Don't Work
1. Check if service supports server-side control
2. Verify active session exists
3. Check for API errors in console
4. Ensure user hasn't revoked permissions

### Queue Not Updating
1. Check session is active
2. Verify tracks exist in database
3. Review queue management logic
4. Check for database connection issues

## Security

- All API endpoints require authentication
- Rate limiting applied to prevent abuse
- OAuth tokens stored securely
- Session IDs use UUID v4 for security
- No playback data shared between users

## Privacy

- Playback history is private to each user
- No cross-user tracking
- Users can delete playback history
- Service usage data aggregated anonymously
- Complies with all service ToS requirements
