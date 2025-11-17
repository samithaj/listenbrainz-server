# Playlist Sync Components

## Overview

The Playlist Sync components provide a unified interface for managing playlists across multiple music streaming services (Spotify, Tidal, YouTube Music, and Apple Music). Users can sync a single ListenBrainz playlist to multiple services simultaneously.

## Components

### PlaylistManager

Main component that provides the complete playlist sync interface.

**Features:**
- Manual sync trigger with service selection
- Force sync option to override sync logic
- Real-time job status monitoring
- Tabbed interface for status and settings
- Integration with user's connected services

**Props:**
```typescript
interface PlaylistManagerProps {
  playlistId: string;           // UUID of the ListenBrainz playlist
  playlistName: string;          // Display name of the playlist
  userConnectedServices: string[]; // List of connected services
}
```

**Usage:**
```tsx
import { PlaylistManager } from "@/musicmatch/components";

function MyPlaylistPage() {
  return (
    <PlaylistManager
      playlistId="abc123..."
      playlistName="My Awesome Playlist"
      userConnectedServices={["spotify", "tidal", "youtube_music"]}
    />
  );
}
```

### PlaylistSyncStatus

Displays current sync status for all connected services.

**Features:**
- Service-specific sync status badges
- Last synced timestamps with relative formatting
- Error message display
- Auto-refresh capability
- Visual service icons

**Props:**
```typescript
interface PlaylistSyncStatusProps {
  playlistId: string;
  onRefresh?: () => void;
}
```

**Sync Statuses:**
- `pending` - Sync queued but not started
- `in_progress` - Currently syncing
- `completed` - Successfully synced
- `failed` - Sync failed with error

**Usage:**
```tsx
import { PlaylistSyncStatus } from "@/musicmatch/components";

function MyComponent() {
  return (
    <PlaylistSyncStatus
      playlistId="abc123..."
      onRefresh={() => console.log("Refreshed!")}
    />
  );
}
```

### PlaylistSyncSettings

Manage sync settings and preferences for a playlist.

**Features:**
- Auto-sync toggle
- Service selection
- Sync frequency configuration
- Settings persistence
- Change detection

**Props:**
```typescript
interface PlaylistSyncSettingsProps {
  playlistId: string;
  availableServices: string[];
  onSettingsUpdate?: (settings: SyncSettings) => void;
}

interface SyncSettings {
  auto_sync_enabled: boolean;
  sync_services: string[];
  sync_frequency_minutes: number;
}
```

**Frequency Options:**
- Every 15 minutes
- Every 30 minutes
- Every hour
- Every 3 hours
- Every 6 hours
- Every 12 hours
- Once a day

**Usage:**
```tsx
import { PlaylistSyncSettings } from "@/musicmatch/components";

function SettingsPage() {
  return (
    <PlaylistSyncSettings
      playlistId="abc123..."
      availableServices={["spotify", "tidal"]}
      onSettingsUpdate={(settings) => {
        console.log("New settings:", settings);
      }}
    />
  );
}
```

## API Integration

The components interact with the following API endpoints:

### Sync Endpoints

**Trigger Sync:**
```
POST /1/musicmatch/playlist/{playlist_id}/sync
Body: {
  "services": ["spotify", "tidal"],
  "force": false
}
Response: {
  "job": {
    "job_id": "...",
    "status": "pending",
    "services": ["spotify", "tidal"]
  }
}
```

**Get Sync Status:**
```
GET /1/musicmatch/playlist/{playlist_id}/sync-status
Response: {
  "mappings": [
    {
      "service": "spotify",
      "external_playlist_id": "...",
      "last_synced": "2025-11-17T10:30:00Z",
      "sync_status": "completed"
    }
  ]
}
```

**Get Job Status:**
```
GET /1/musicmatch/playlist/jobs/{job_id}
Response: {
  "job": {
    "job_id": "...",
    "status": "completed",
    "success_count": 2,
    "failure_count": 0
  }
}
```

### Settings Endpoints

**Get Settings:**
```
GET /1/musicmatch/playlist/{playlist_id}/sync-settings
Response: {
  "settings": {
    "auto_sync_enabled": true,
    "sync_services": ["spotify", "tidal"],
    "sync_frequency_minutes": 60
  }
}
```

**Update Settings:**
```
POST /1/musicmatch/playlist/{playlist_id}/sync-settings
Body: {
  "auto_sync_enabled": true,
  "sync_services": ["spotify"],
  "sync_frequency_minutes": 180
}
```

## Integration Guide

### Adding to Existing Playlist Page

```tsx
import React from "react";
import { PlaylistManager } from "@/musicmatch/components";
import { useCurrentUser } from "@/utils/GlobalAppContext";

export default function PlaylistPage({ playlist }) {
  const { currentUser } = useCurrentUser();

  // Extract connected services from user context
  const connectedServices = [];
  if (currentUser.spotifyAuth) connectedServices.push("spotify");
  if (currentUser.tidalAuth) connectedServices.push("tidal");
  if (currentUser.youtubeMusicAuth) connectedServices.push("youtube_music");
  if (currentUser.appleAuth) connectedServices.push("apple");

  return (
    <div>
      {/* Existing playlist content */}
      <h1>{playlist.name}</h1>
      <TrackList tracks={playlist.tracks} />

      {/* Add playlist sync manager */}
      <div className="mt-4">
        <PlaylistManager
          playlistId={playlist.id}
          playlistName={playlist.name}
          userConnectedServices={connectedServices}
        />
      </div>
    </div>
  );
}
```

### Standalone Sync Status Widget

```tsx
import React from "react";
import { PlaylistSyncStatus } from "@/musicmatch/components";

export default function SyncWidget({ playlistId }) {
  return (
    <div className="card">
      <div className="card-body">
        <PlaylistSyncStatus playlistId={playlistId} />
      </div>
    </div>
  );
}
```

## Styling

The components use Bootstrap 5 classes and Font Awesome icons. Ensure these are available:

```html
<!-- Bootstrap CSS -->
<link rel="stylesheet" href="...bootstrap.css" />

<!-- Font Awesome -->
<link rel="stylesheet" href="...font-awesome.css" />
```

### Service Icons

The components use these Font Awesome icons for services:
- Spotify: `fa-spotify`
- Tidal: `fa-music`
- YouTube Music: `fa-youtube`
- Apple Music: `fa-apple`

## Error Handling

All components include comprehensive error handling:

1. **Network Errors**: Display error alerts with retry buttons
2. **API Errors**: Show user-friendly error messages via toast notifications
3. **Loading States**: Show spinners during async operations
4. **Empty States**: Guide users when no data is available

## State Management

Components use React hooks for state management:
- `useState` for local component state
- `useEffect` for data fetching and side effects
- No external state management library required

## Accessibility

- Semantic HTML structure
- ARIA labels where appropriate
- Keyboard navigation support
- Focus management
- Screen reader friendly status messages

## Performance Considerations

1. **Polling**: Job status polling stops after completion or 5 minutes
2. **Debouncing**: Settings changes are not saved until user clicks "Save"
3. **Lazy Loading**: Only active tab content is rendered
4. **Minimal Re-renders**: State updates are optimized to prevent unnecessary renders

## Testing

### Unit Tests Example

```typescript
import { render, screen, fireEvent } from "@testing-library/react";
import PlaylistSyncStatus from "./PlaylistSyncStatus";

test("displays sync status for connected services", async () => {
  render(<PlaylistSyncStatus playlistId="test-123" />);

  // Wait for data to load
  await screen.findByText("Spotify");

  // Check status badge
  expect(screen.getByText("completed")).toBeInTheDocument();
});
```

## Future Enhancements

1. **Conflict Resolution**: Handle conflicts when same playlist is modified on multiple services
2. **Selective Track Sync**: Allow users to exclude specific tracks from sync
3. **Sync History**: Show detailed sync history with timestamps and changes
4. **Batch Operations**: Sync multiple playlists at once
5. **Webhook Support**: Real-time updates via webhooks instead of polling
6. **Custom Mapping**: Allow manual track mapping for failed matches

## Troubleshooting

### Sync Not Starting

- Check that user is authenticated with selected services
- Verify OAuth tokens are not expired
- Check browser console for error messages

### Sync Stuck in Progress

- Job polling stops after 5 minutes
- Refresh the page to check updated status
- Check server logs for job processing errors

### Service Not Available

- User needs to connect service in Settings > Music Services
- Ensure OAuth credentials are configured in backend
- Verify service API is not experiencing downtime

## Support

For issues or questions:
1. Check the main [MusicMatch README](./README.md)
2. Review API documentation
3. Check server logs for detailed error messages
4. File an issue on the ListenBrainz GitHub repository
