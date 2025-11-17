# MusicMatch: Unified Music Graph & Multi-Service Integration

## Executive Summary

**Goal:** Build MusicMatch as an extension of listenbrainz-server that adds:

- Multi-service integration (Spotify, YouTube Music, Apple Music, Tidal, Last.fm)
- Interactive graph visualization (genre/artist/track relationships)
- Unified playlist management (create once, sync everywhere)
- Enhanced in-app playback (seamless cross-service playback)

**Approach:** Extend the existing listenbrainz frontend with new menus, pages, and backend APIs while reusing existing infrastructure for OAuth, playback, playlists, and visualizations.

---

## Phase 1: Foundation & Multi-Service Integration (2-3 weeks)

### 1.1 Backend: Extend OAuth System

#### Files to Modify:
- `listenbrainz-server/data/model/external_service.py`
- `listenbrainz-server/listenbrainz/db/external_service_oauth.py`
- `listenbrainz-server/listenbrainz/webserver/views/settings.py`

#### Tasks:

**A. Add Tidal & YouTube Music to service types**

File: `data/model/external_service.py`

```python
class ExternalServiceType(Enum):
    # ... existing services ...
    TIDAL = 'tidal'
    YOUTUBE_MUSIC = 'youtube_music'  # Separate from YouTube
```

- [ ] Add `TIDAL` enum value to `ExternalServiceType`
- [ ] Add `YOUTUBE_MUSIC` enum value to `ExternalServiceType`
- [ ] Update any service type validation logic
- [ ] Add service-specific configuration (API endpoints, scopes, etc.)

**B. Create OAuth callback handlers**

File: `listenbrainz/webserver/views/settings.py`

```python
@settings_bp.route('/music-services/tidal/callback/')
def tidal_callback():
    # OAuth flow for Tidal
    # Store tokens in external_service_oauth table
    pass

@settings_bp.route('/music-services/youtube-music/callback/')
def youtube_music_callback():
    # OAuth flow for YouTube Music
    pass
```

- [ ] Implement Tidal OAuth callback handler
  - [ ] Handle authorization code exchange
  - [ ] Store access token and refresh token
  - [ ] Handle error cases
  - [ ] Redirect to settings page with success/error message
- [ ] Implement YouTube Music OAuth callback handler
  - [ ] Handle authorization code exchange
  - [ ] Store access token and refresh token
  - [ ] Handle error cases
  - [ ] Redirect to settings page with success/error message
- [ ] Add OAuth initiation routes (`/music-services/tidal/connect`, etc.)
- [ ] Register OAuth apps with Tidal and YouTube Music
- [ ] Add API credentials to configuration

**C. Token refresh handlers**

Create directory: `listenbrainz/background/token_refresh/`

Files to create:
- `tidal_token_refresher.py`
- `youtube_music_token_refresher.py`

- [ ] Create token refresh worker for Tidal
  - [ ] Implement automatic token refresh before expiry
  - [ ] Handle refresh failures
  - [ ] Log token refresh events
  - [ ] Schedule periodic checks
- [ ] Create token refresh worker for YouTube Music
  - [ ] Implement automatic token refresh before expiry
  - [ ] Handle refresh failures
  - [ ] Log token refresh events
  - [ ] Schedule periodic checks
- [ ] Add workers to background task scheduler
- [ ] Add monitoring/alerting for token refresh failures

---

### 1.2 Frontend: Add Service Connection UI

#### Files to Modify:
- `frontend/js/src/settings/music-services/details/MusicServices.tsx`
- `frontend/js/src/utils/GlobalAppContext.tsx`

#### Tasks:

**A. Add Tidal & YouTube Music cards to settings**

File: `frontend/js/src/settings/music-services/details/MusicServices.tsx`

```tsx
<ServiceCard
  service="tidal"
  icon="tidal-logo.svg"
  name="Tidal"
  description="Connect Tidal for high-quality streaming and library sync"
/>

<ServiceCard
  service="youtube_music"
  icon="youtube-music-logo.svg"
  name="YouTube Music"
  description="Connect YouTube Music for playback and playlists"
/>
```

- [ ] Add Tidal service card component
  - [ ] Add Tidal logo to static assets
  - [ ] Implement connect/disconnect functionality
  - [ ] Show connection status
  - [ ] Display service-specific settings
- [ ] Add YouTube Music service card component
  - [ ] Add YouTube Music logo to static assets
  - [ ] Implement connect/disconnect functionality
  - [ ] Show connection status
  - [ ] Display service-specific settings
- [ ] Update service list layout to accommodate new services
- [ ] Add connection status indicators
- [ ] Implement error handling and user feedback

**B. Update GlobalAppContext types**

File: `frontend/js/src/utils/GlobalAppContext.tsx`

```tsx
interface GlobalAppContextT {
  // ... existing ...
  tidalAuth?: UserToken;
  youtubeMusicAuth?: UserToken;
}
```

- [ ] Add `tidalAuth` to global context interface
- [ ] Add `youtubeMusicAuth` to global context interface
- [ ] Update context provider to fetch new auth tokens
- [ ] Add TypeScript types for service-specific token data
- [ ] Update any components that depend on service auth state

---

### 1.3 API Service: Cross-Service Track Resolution

#### New File:
`listenbrainz/webserver/views/musicmatch_api.py`

#### Blueprint Registration:

File: `listenbrainz/webserver/__init__.py`

```python
from listenbrainz.webserver.views import musicmatch_api

app.register_blueprint(musicmatch_api.musicmatch_api_bp)
```

- [ ] Create musicmatch_api blueprint
- [ ] Register blueprint in Flask app

#### Key Endpoints:

**Endpoint 1: GET /1/musicmatch/track/<recording_mbid>/services**

Returns available service IDs for a track

Response example:
```json
{
  "spotify_id": "3n3Ppam7vgaVa1iaRUc9Lp",
  "youtube_id": "dQw4w9WgXcQ",
  "apple_music_id": "1234567890",
  "tidal_id": "12345678"
}
```

- [ ] Implement endpoint handler
- [ ] Query track_service_mapping table
- [ ] Return all available service IDs for given MBID
- [ ] Handle missing/invalid MBID
- [ ] Add authentication/rate limiting
- [ ] Add API documentation

**Endpoint 2: POST /1/musicmatch/track/resolve**

Resolve track across services by fuzzy matching

Request body:
```json
{
  "track_name": "Bohemian Rhapsody",
  "artist_name": "Queen",
  "services": ["spotify", "tidal", "youtube_music"]
}
```

- [ ] Implement endpoint handler
- [ ] Implement fuzzy matching algorithm
  - [ ] Match by track name + artist
  - [ ] Handle variations in track/artist names
  - [ ] Calculate confidence scores
- [ ] Query each requested service's API
- [ ] Cache results in track_service_mapping table
- [ ] Return matched track IDs with confidence scores
- [ ] Handle service API failures gracefully
- [ ] Add authentication/rate limiting
- [ ] Add API documentation

#### Database Schema:

File: `admin/timescale/updates/2024-xx-xx-musicmatch-track-mapping.sql`

```sql
CREATE TABLE musicmatch.track_service_mapping (
    recording_mbid UUID NOT NULL,
    service external_service_oauth_type NOT NULL,
    external_track_id TEXT NOT NULL,
    confidence FLOAT,  -- 0.0 to 1.0 matching confidence
    last_verified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (recording_mbid, service)
);

CREATE INDEX idx_track_mapping_service
ON musicmatch.track_service_mapping(service, external_track_id);
```

- [ ] Create database migration file
- [ ] Create `musicmatch` schema if it doesn't exist
- [ ] Create `track_service_mapping` table
- [ ] Create index on service + external_track_id
- [ ] Add foreign key constraint to recording MBID
- [ ] Test migration on development database
- [ ] Document schema in database documentation
- [ ] Plan for data backfill strategy

---

## Phase 2: Graph Visualization (3-4 weeks)

### 2.1 Backend: Graph Data Generation

#### New Files:
- `listenbrainz/background/graph_generator/user_music_graph.py`
- `listenbrainz/background/graph_generator/artist_relations.py`
- `listenbrainz/background/graph_generator/genre_graph.py`

#### Tasks:

**A. User Music Graph Generator**

File: `listenbrainz/background/graph_generator/user_music_graph.py`

- [ ] Create user music graph generator module
- [ ] Implement graph building from user listening history
  - [ ] Query user's top artists
  - [ ] Query user's top tracks
  - [ ] Query user's top genres
  - [ ] Calculate relationships and weights
- [ ] Generate graph nodes (artists, tracks, genres)
- [ ] Generate graph edges (relationships between nodes)
- [ ] Calculate edge weights based on listening patterns
- [ ] Store graph data in efficient format (JSON/GraphML)
- [ ] Implement caching strategy
- [ ] Schedule periodic graph regeneration
- [ ] Add configuration for graph parameters (depth, node limits, etc.)

**B. Artist Relations Graph**

File: `listenbrainz/background/graph_generator/artist_relations.py`

- [ ] Create artist relations module
- [ ] Query MusicBrainz for artist relationships
  - [ ] Collaborations
  - [ ] Band memberships
  - [ ] Similar artists
- [ ] Integrate with ListenBrainz similarity data
- [ ] Calculate relationship strength scores
- [ ] Generate artist relationship graph
- [ ] Store relationship data in database
- [ ] Implement incremental updates
- [ ] Add API to query artist relationships

**C. Genre Graph**

File: `listenbrainz/background/graph_generator/genre_graph.py`

- [ ] Create genre graph module
- [ ] Build genre taxonomy from MusicBrainz tags
- [ ] Calculate genre-to-genre relationships
- [ ] Map tracks/artists to genres
- [ ] Generate genre hierarchy graph
- [ ] Calculate genre popularity scores
- [ ] Store genre graph data
- [ ] Implement periodic updates
- [ ] Add API to query genre relationships

---

### 2.2 Frontend: Interactive Graph Visualization

#### New Files/Components:
- `frontend/js/src/musicmatch/components/MusicGraph.tsx`
- `frontend/js/src/musicmatch/components/GraphNode.tsx`
- `frontend/js/src/musicmatch/components/GraphControls.tsx`
- `frontend/js/src/musicmatch/utils/graphLayout.ts`

#### Tasks:

**A. Graph Visualization Component**

- [ ] Install graph visualization library (e.g., D3.js, vis.js, react-force-graph)
- [ ] Create main `MusicGraph` component
  - [ ] Implement graph rendering
  - [ ] Add zoom/pan controls
  - [ ] Implement node interactions (click, hover)
  - [ ] Add filtering options
  - [ ] Implement search functionality
- [ ] Create `GraphNode` component
  - [ ] Display node information
  - [ ] Add node-specific styling (artist vs track vs genre)
  - [ ] Implement node selection
  - [ ] Add tooltips with node details
- [ ] Create `GraphControls` component
  - [ ] Layout algorithm selection
  - [ ] Filter controls
  - [ ] Depth/complexity controls
  - [ ] Color scheme options
  - [ ] Export options

**B. Graph Layout Algorithms**

File: `frontend/js/src/musicmatch/utils/graphLayout.ts`

- [ ] Implement force-directed layout
- [ ] Implement hierarchical layout
- [ ] Implement circular layout
- [ ] Add layout transition animations
- [ ] Optimize performance for large graphs
- [ ] Add layout persistence (save user's preferred layout)

**C. Graph Data Integration**

- [ ] Create API service for fetching graph data
- [ ] Implement data loading states
- [ ] Add error handling
- [ ] Implement graph data caching
- [ ] Add real-time updates for user's listening activity
- [ ] Optimize data transfer (compression, pagination)

---

### 2.3 Graph API Endpoints

#### New Endpoints in `musicmatch_api.py`:

**GET /1/musicmatch/graph/user/<user_name>**

- [ ] Implement endpoint to fetch user's music graph
- [ ] Support filtering by time range
- [ ] Support depth/complexity parameters
- [ ] Return graph in standard format (nodes + edges)
- [ ] Add pagination for large graphs
- [ ] Implement caching
- [ ] Add rate limiting
- [ ] Document API

**GET /1/musicmatch/graph/artist/<artist_mbid>**

- [ ] Implement endpoint to fetch artist relationship graph
- [ ] Include related artists
- [ ] Include collaborators
- [ ] Include genre connections
- [ ] Support depth parameter
- [ ] Return graph in standard format
- [ ] Add caching
- [ ] Document API

**GET /1/musicmatch/graph/genre/<genre_name>**

- [ ] Implement endpoint to fetch genre graph
- [ ] Include related genres
- [ ] Include top artists in genre
- [ ] Include top tracks in genre
- [ ] Support filtering parameters
- [ ] Return graph in standard format
- [ ] Add caching
- [ ] Document API

---

### 2.4 Database Schema for Graph Data

#### New Tables:

File: `admin/timescale/updates/2024-xx-xx-musicmatch-graph-schema.sql`

```sql
-- User music graphs (cached)
CREATE TABLE musicmatch.user_music_graph (
    user_id INTEGER NOT NULL,
    graph_type TEXT NOT NULL,  -- 'artist', 'track', 'genre', 'combined'
    time_range TEXT,  -- 'week', 'month', 'year', 'all_time'
    graph_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, graph_type, time_range)
);

-- Artist relationships
CREATE TABLE musicmatch.artist_relationships (
    artist_mbid_1 UUID NOT NULL,
    artist_mbid_2 UUID NOT NULL,
    relationship_type TEXT NOT NULL,  -- 'collaboration', 'similar', 'member_of'
    strength FLOAT,  -- 0.0 to 1.0
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (artist_mbid_1, artist_mbid_2, relationship_type)
);

-- Genre taxonomy
CREATE TABLE musicmatch.genre_hierarchy (
    genre_name TEXT PRIMARY KEY,
    parent_genre TEXT,
    level INTEGER,
    popularity_score FLOAT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_genre_parent ON musicmatch.genre_hierarchy(parent_genre);
```

- [ ] Create database migration
- [ ] Create user_music_graph table
- [ ] Create artist_relationships table
- [ ] Create genre_hierarchy table
- [ ] Add appropriate indexes
- [ ] Test migration
- [ ] Document schema

---

## Phase 3: Unified Playlist Management (2-3 weeks)

### 3.1 Backend: Multi-Service Playlist Sync

#### New Files:
- `listenbrainz/background/playlist_sync/sync_manager.py`
- `listenbrainz/background/playlist_sync/spotify_sync.py`
- `listenbrainz/background/playlist_sync/tidal_sync.py`
- `listenbrainz/background/playlist_sync/youtube_music_sync.py`
- `listenbrainz/background/playlist_sync/apple_music_sync.py`

#### Tasks:

**A. Playlist Sync Manager**

- [ ] Create sync manager module
- [ ] Implement playlist sync orchestration
- [ ] Track sync status per service
- [ ] Handle sync conflicts
- [ ] Implement retry logic for failed syncs
- [ ] Add sync scheduling
- [ ] Log sync operations
- [ ] Send sync status updates to frontend

**B. Service-Specific Sync Implementations**

- [ ] Implement Spotify playlist sync
  - [ ] Create playlists on Spotify
  - [ ] Add/remove tracks
  - [ ] Update playlist metadata
  - [ ] Handle track matching
- [ ] Implement Tidal playlist sync
  - [ ] Create playlists on Tidal
  - [ ] Add/remove tracks
  - [ ] Update playlist metadata
  - [ ] Handle track matching
- [ ] Implement YouTube Music playlist sync
  - [ ] Create playlists on YouTube Music
  - [ ] Add/remove tracks
  - [ ] Update playlist metadata
  - [ ] Handle track matching
- [ ] Implement Apple Music playlist sync
  - [ ] Create playlists on Apple Music
  - [ ] Add/remove tracks
  - [ ] Update playlist metadata
  - [ ] Handle track matching

**C. Sync API Endpoints**

New endpoints in `musicmatch_api.py`:

- [ ] POST /1/musicmatch/playlist/<playlist_id>/sync
  - [ ] Trigger sync to specified services
  - [ ] Return sync job ID
  - [ ] Queue background sync job
- [ ] GET /1/musicmatch/playlist/<playlist_id>/sync-status
  - [ ] Return sync status for all services
  - [ ] Include last sync time
  - [ ] Include error messages if any
- [ ] POST /1/musicmatch/playlist/<playlist_id>/sync-settings
  - [ ] Configure auto-sync settings
  - [ ] Set sync frequency
  - [ ] Enable/disable specific services

---

### 3.2 Database Schema for Playlist Sync

File: `admin/timescale/updates/2024-xx-xx-musicmatch-playlist-sync.sql`

```sql
CREATE TABLE musicmatch.playlist_sync_mapping (
    lb_playlist_id UUID NOT NULL,
    service external_service_oauth_type NOT NULL,
    external_playlist_id TEXT NOT NULL,
    last_synced TIMESTAMP WITH TIME ZONE,
    sync_status TEXT,  -- 'pending', 'in_progress', 'completed', 'failed'
    error_message TEXT,
    PRIMARY KEY (lb_playlist_id, service)
);

CREATE TABLE musicmatch.playlist_sync_settings (
    lb_playlist_id UUID PRIMARY KEY,
    auto_sync_enabled BOOLEAN DEFAULT TRUE,
    sync_services TEXT[],  -- Array of service names
    sync_frequency_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

- [ ] Create migration file
- [ ] Create playlist_sync_mapping table
- [ ] Create playlist_sync_settings table
- [ ] Add indexes
- [ ] Test migration
- [ ] Document schema

---

### 3.3 Frontend: Playlist Management UI

#### New Components:
- `frontend/js/src/musicmatch/playlists/PlaylistManager.tsx`
- `frontend/js/src/musicmatch/playlists/PlaylistSyncStatus.tsx`
- `frontend/js/src/musicmatch/playlists/PlaylistSyncSettings.tsx`

#### Tasks:

**A. Playlist Manager Component**

- [ ] Create playlist manager UI
- [ ] List all user playlists
- [ ] Show sync status for each service
- [ ] Add "Sync Now" button
- [ ] Add playlist creation from existing service playlists
- [ ] Show track count and metadata
- [ ] Implement playlist filtering/search

**B. Sync Status Component**

- [ ] Create sync status indicator component
- [ ] Show sync progress
- [ ] Display last sync time
- [ ] Show service-specific status
- [ ] Display sync errors with details
- [ ] Add retry failed sync option

**C. Sync Settings Component**

- [ ] Create sync settings UI
- [ ] Toggle auto-sync on/off
- [ ] Select services to sync with
- [ ] Set sync frequency
- [ ] Configure conflict resolution preferences
- [ ] Save settings

---

## Phase 4: Enhanced In-App Playback (2-3 weeks)

### 4.1 Backend: Unified Playback API

#### New Files:
- `listenbrainz/background/playback/playback_router.py`
- `listenbrainz/background/playback/service_players/`
  - `spotify_player.py`
  - `tidal_player.py`
  - `youtube_music_player.py`
  - `apple_music_player.py`

#### Tasks:

**A. Playback Router**

- [ ] Create playback router module
- [ ] Implement service selection logic
  - [ ] Check service availability
  - [ ] Check track availability on each service
  - [ ] Prefer user's default service
  - [ ] Fallback to other services
- [ ] Handle playback state management
- [ ] Track currently playing track
- [ ] Implement playback queue management
- [ ] Add crossfade support (if services support)
- [ ] Log playback events

**B. Service-Specific Players**

- [ ] Implement Spotify player integration
  - [ ] Use Spotify Web Playback SDK
  - [ ] Handle playback controls
  - [ ] Report playback state
- [ ] Implement Tidal player integration
  - [ ] Integrate Tidal SDK
  - [ ] Handle playback controls
  - [ ] Report playback state
- [ ] Implement YouTube Music player integration
  - [ ] Use YouTube iframe API or Music API
  - [ ] Handle playback controls
  - [ ] Report playback state
- [ ] Implement Apple Music player integration
  - [ ] Use MusicKit JS
  - [ ] Handle playback controls
  - [ ] Report playback state

**C. Playback API Endpoints**

New endpoints in `musicmatch_api.py`:

- [ ] POST /1/musicmatch/playback/play
  - [ ] Start playback of specified track
  - [ ] Select best available service
  - [ ] Return playback session info
- [ ] POST /1/musicmatch/playback/pause
  - [ ] Pause current playback
- [ ] POST /1/musicmatch/playback/resume
  - [ ] Resume paused playback
- [ ] POST /1/musicmatch/playback/skip
  - [ ] Skip to next track in queue
- [ ] GET /1/musicmatch/playback/status
  - [ ] Return current playback state
  - [ ] Include track info
  - [ ] Include service being used
- [ ] POST /1/musicmatch/playback/queue
  - [ ] Add tracks to playback queue
- [ ] GET /1/musicmatch/playback/queue
  - [ ] Get current playback queue

---

### 4.2 Frontend: Unified Playback UI

#### New Components:
- `frontend/js/src/musicmatch/playback/UnifiedPlayer.tsx`
- `frontend/js/src/musicmatch/playback/PlaybackQueue.tsx`
- `frontend/js/src/musicmatch/playback/ServiceSelector.tsx`
- `frontend/js/src/musicmatch/playback/NowPlaying.tsx`

#### Tasks:

**A. Unified Player Component**

- [ ] Create main player UI component
- [ ] Integrate all service players
- [ ] Implement playback controls
  - [ ] Play/pause button
  - [ ] Skip forward/back buttons
  - [ ] Seek bar
  - [ ] Volume control
- [ ] Display current track info
  - [ ] Track name
  - [ ] Artist name
  - [ ] Album art
  - [ ] Service icon
- [ ] Show playback progress
- [ ] Add service switching controls

**B. Playback Queue Component**

- [ ] Create queue UI
- [ ] Display queued tracks
- [ ] Implement drag-and-drop reordering
- [ ] Add remove from queue option
- [ ] Show track availability per service
- [ ] Add "Play next" functionality

**C. Service Selector Component**

- [ ] Create service selector UI
- [ ] Show available services for current track
- [ ] Allow manual service selection
- [ ] Display service quality/bitrate info
- [ ] Remember user's service preferences

**D. Now Playing Component**

- [ ] Create expanded now playing view
- [ ] Display full track details
- [ ] Show lyrics (if available)
- [ ] Display related tracks
- [ ] Add to playlist functionality
- [ ] Share current track option

---

### 4.3 Database Schema for Playback

File: `admin/timescale/updates/2024-xx-xx-musicmatch-playback.sql`

```sql
CREATE TABLE musicmatch.playback_sessions (
    session_id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    service external_service_oauth_type NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "user"(id)
);

CREATE TABLE musicmatch.playback_queue (
    session_id UUID NOT NULL,
    position INTEGER NOT NULL,
    recording_mbid UUID NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    played_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (session_id, position),
    FOREIGN KEY (session_id) REFERENCES musicmatch.playback_sessions(session_id)
);

CREATE INDEX idx_playback_user ON musicmatch.playback_sessions(user_id, started_at);
```

- [ ] Create migration file
- [ ] Create playback_sessions table
- [ ] Create playback_queue table
- [ ] Add indexes
- [ ] Test migration
- [ ] Document schema

---

## Phase 5: Navigation & Integration (1-2 weeks)

### 5.1 Main Navigation Menu

#### Files to Modify:
- `frontend/js/src/components/Navbar.tsx`
- `frontend/js/src/utils/routes.ts`

#### Tasks:

- [ ] Add "MusicMatch" menu item to main navigation
- [ ] Create submenu structure:
  - [ ] Dashboard
  - [ ] Music Graph
  - [ ] Playlists
  - [ ] Discovery
  - [ ] Services
- [ ] Add MusicMatch icon/logo
- [ ] Implement responsive mobile menu
- [ ] Add feature flags for gradual rollout

---

### 5.2 Routing Setup

#### New Files:
- `frontend/js/src/musicmatch/MusicMatchRoutes.tsx`
- `frontend/js/src/musicmatch/pages/Dashboard.tsx`
- `frontend/js/src/musicmatch/pages/GraphExplorer.tsx`
- `frontend/js/src/musicmatch/pages/PlaylistManager.tsx`
- `frontend/js/src/musicmatch/pages/Discovery.tsx`

#### Tasks:

**A. Create Route Configuration**

- [ ] Set up MusicMatch route structure
- [ ] Define route paths:
  - `/musicmatch` - Dashboard
  - `/musicmatch/graph` - Graph Explorer
  - `/musicmatch/playlists` - Playlist Manager
  - `/musicmatch/discovery` - Discovery page
  - `/musicmatch/services` - Service management
- [ ] Add route guards (authentication required)
- [ ] Implement lazy loading for routes

**B. Create Page Components**

- [ ] Create Dashboard page
  - [ ] Recent activity summary
  - [ ] Connected services status
  - [ ] Quick stats
  - [ ] Recent playlists
- [ ] Create Graph Explorer page
  - [ ] Graph visualization component
  - [ ] Filtering controls
  - [ ] Graph type selector
- [ ] Create Playlist Manager page
  - [ ] Playlist list
  - [ ] Sync controls
  - [ ] Playlist creation
- [ ] Create Discovery page
  - [ ] Recommendations from multiple services
  - [ ] Trending tracks/artists
  - [ ] Genre exploration

---

### 5.3 Integration with Existing Features

#### Tasks:

**A. Listen History Integration**

- [ ] Add "Play on..." buttons to listen history items
- [ ] Show track availability indicators
- [ ] Add to playlist from history
- [ ] View track in graph explorer

**B. Playlist Integration**

- [ ] Add sync controls to existing playlist pages
- [ ] Show multi-service sync status
- [ ] Enable sync on existing playlists
- [ ] Add service-specific track links

**C. Statistics Integration**

- [ ] Integrate multi-service listening data into stats
- [ ] Compare listening patterns across services
- [ ] Show service usage statistics
- [ ] Generate unified listening reports

**D. Recommendations Integration**

- [ ] Enhance recommendations with multi-service data
- [ ] Show recommendations from each connected service
- [ ] Aggregate similar recommendations
- [ ] Allow playing recommendations on any service

---

## Phase 6: Testing & Deployment (2-3 weeks)

### 6.1 Testing

#### Backend Testing

- [ ] Write unit tests for OAuth flows
- [ ] Write unit tests for track resolution
- [ ] Write unit tests for playlist sync
- [ ] Write unit tests for playback routing
- [ ] Write integration tests for service APIs
- [ ] Write integration tests for graph generation
- [ ] Test database migrations
- [ ] Test background workers
- [ ] Performance testing for graph queries
- [ ] Load testing for API endpoints

#### Frontend Testing

- [ ] Write component tests for UI components
- [ ] Write integration tests for user flows
- [ ] Test cross-browser compatibility
- [ ] Test responsive layouts
- [ ] Test accessibility (WCAG compliance)
- [ ] Test error handling and edge cases
- [ ] Test loading states
- [ ] Test with different service combinations

---

### 6.2 Documentation

- [ ] API documentation
  - [ ] Document all MusicMatch endpoints
  - [ ] Add request/response examples
  - [ ] Document authentication requirements
  - [ ] Add rate limiting details
- [ ] User documentation
  - [ ] Create setup guide for connecting services
  - [ ] Create playlist sync guide
  - [ ] Create graph explorer guide
  - [ ] Create playback guide
  - [ ] Add FAQ section
  - [ ] Add troubleshooting guide
- [ ] Developer documentation
  - [ ] Document architecture
  - [ ] Document database schema
  - [ ] Document background workers
  - [ ] Add contribution guidelines
  - [ ] Document service integration patterns

---

### 6.3 Deployment Checklist

#### Configuration

- [ ] Set up OAuth apps for all services
  - [ ] Spotify
  - [ ] Tidal
  - [ ] YouTube Music
  - [ ] Apple Music
- [ ] Configure API credentials in production
- [ ] Set up environment variables
- [ ] Configure rate limits
- [ ] Set up monitoring and alerting

#### Database

- [ ] Run migrations on staging
- [ ] Verify migrations on staging
- [ ] Plan for production migration
- [ ] Set up database backups
- [ ] Configure TimescaleDB retention policies

#### Backend Services

- [ ] Deploy API changes
- [ ] Deploy background workers
- [ ] Configure worker schedules
- [ ] Set up service monitoring
- [ ] Configure error tracking (Sentry, etc.)
- [ ] Set up performance monitoring

#### Frontend

- [ ] Build production assets
- [ ] Test production build
- [ ] Deploy frontend changes
- [ ] Update CDN cache
- [ ] Verify asset loading

#### Infrastructure

- [ ] Configure load balancers
- [ ] Set up auto-scaling policies
- [ ] Configure caching layers (Redis, etc.)
- [ ] Set up log aggregation
- [ ] Configure backup systems

---

### 6.4 Gradual Rollout Plan

- [ ] Phase 1: Internal testing (dev team)
  - [ ] Enable for dev/staging environments
  - [ ] Test all functionality
  - [ ] Fix critical bugs
- [ ] Phase 2: Beta testing (selected users)
  - [ ] Enable feature flag for beta users
  - [ ] Gather feedback
  - [ ] Monitor performance
  - [ ] Address issues
- [ ] Phase 3: Limited rollout (10% of users)
  - [ ] Enable for 10% of user base
  - [ ] Monitor metrics
  - [ ] Check error rates
  - [ ] Verify performance
- [ ] Phase 4: Expanded rollout (50% of users)
  - [ ] Enable for 50% of user base
  - [ ] Continue monitoring
  - [ ] Address any issues
- [ ] Phase 5: Full rollout (100% of users)
  - [ ] Enable for all users
  - [ ] Announce feature
  - [ ] Monitor closely
  - [ ] Support user questions

---

## Success Metrics

### User Engagement

- [ ] Track number of connected services per user
- [ ] Monitor playlist sync usage
- [ ] Track graph explorer page views
- [ ] Monitor playback sessions
- [ ] Track cross-service plays

### Technical Performance

- [ ] API response times < 200ms (p95)
- [ ] Graph generation time < 5 seconds
- [ ] Playlist sync success rate > 95%
- [ ] Track resolution accuracy > 90%
- [ ] Background worker health > 99%

### Feature Adoption

- [ ] Percentage of users connecting multiple services
- [ ] Percentage of playlists with sync enabled
- [ ] Daily active users using graph explorer
- [ ] Number of cross-service plays per day

---

## Future Enhancements (Post-Launch)

### Additional Features

- [ ] Social features
  - [ ] Share music graphs with friends
  - [ ] Compare music tastes
  - [ ] Collaborative playlists across services
- [ ] Advanced recommendations
  - [ ] ML-powered recommendations
  - [ ] Cross-service discovery
  - [ ] Mood-based playlists
- [ ] Analytics dashboard
  - [ ] Detailed listening patterns
  - [ ] Service comparison analytics
  - [ ] Genre evolution over time
- [ ] Mobile app integration
  - [ ] Native mobile player
  - [ ] Offline mode
  - [ ] Background playback
- [ ] Additional service integrations
  - [ ] Deezer
  - [ ] Pandora
  - [ ] SoundCloud
  - [ ] Bandcamp

### Performance Optimizations

- [ ] Graph caching strategies
- [ ] Service API call optimization
- [ ] Database query optimization
- [ ] Frontend bundle size reduction
- [ ] Image optimization

### Scalability Improvements

- [ ] Horizontal scaling for workers
- [ ] Distributed graph processing
- [ ] CDN for static assets
- [ ] Database sharding strategies
- [ ] Microservices architecture considerations

---

## Dependencies & Prerequisites

### External Services

- [ ] Spotify Developer Account & API access
- [ ] Tidal Developer Account & API access
- [ ] YouTube Music API access
- [ ] Apple Music Developer Program & MusicKit
- [ ] Last.fm API access (if needed)

### Technical Requirements

- [ ] TimescaleDB (already in use)
- [ ] Redis (for caching)
- [ ] Graph visualization library
- [ ] Service SDKs:
  - [ ] Spotify Web API
  - [ ] Tidal SDK
  - [ ] YouTube Music API client
  - [ ] MusicKit JS (Apple Music)

### Team Skills Required

- [ ] Backend: Python, Flask, PostgreSQL
- [ ] Frontend: React, TypeScript, D3.js/graph visualization
- [ ] OAuth 2.0 implementation
- [ ] Graph algorithms
- [ ] Music metadata and matching
- [ ] API integration experience

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|---------|-----------|------------|
| Service API rate limits | High | High | Implement request caching, queue systems |
| Track matching inaccuracy | Medium | Medium | Implement multiple matching strategies, manual correction |
| OAuth token management | High | Medium | Automated refresh, monitoring, alerts |
| Graph performance at scale | High | Medium | Caching, pagination, pre-computation |
| Service API changes | Medium | Low | Version monitoring, graceful degradation |

### Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|---------|-----------|------------|
| Low user adoption | High | Medium | Beta testing, user feedback, marketing |
| Service API costs | Medium | Low | Monitor usage, optimize API calls |
| Privacy concerns | High | Low | Clear privacy policy, user controls |
| Service availability | Medium | Medium | Fallback mechanisms, status monitoring |

---

## Notes

- This project extends ListenBrainz-Server by reusing existing infrastructure
- OAuth system already supports Spotify, YouTube, SoundCloud, Apple Music - we're adding Tidal and YouTube Music (as separate from YouTube)
- Existing playlist functionality can be extended for multi-service sync
- Leverage existing BrainzPlayer for playback foundation
- MusicBrainz data provides foundation for track resolution
- Consider privacy implications of cross-service data aggregation
- Ensure compliance with each service's terms of service
- Plan for graceful degradation when services are unavailable

---

## References

- ListenBrainz API Documentation: https://listenbrainz.readthedocs.io/
- Spotify Web API: https://developer.spotify.com/documentation/web-api/
- Tidal API Documentation: https://developer.tidal.com/
- YouTube Music API: https://developers.google.com/youtube/
- Apple MusicKit: https://developer.apple.com/musickit/
- MusicBrainz Database: https://musicbrainz.org/doc/MusicBrainz_Database
