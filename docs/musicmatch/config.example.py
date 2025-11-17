# MusicMatch Configuration Example
# Copy this to your config.py and update with your credentials

# ============================================================================
# Spotify Configuration
# ============================================================================
# Register your app at: https://developer.spotify.com/dashboard

SPOTIFY_CLIENT_ID = "your-spotify-client-id-here"
SPOTIFY_CLIENT_SECRET = "your-spotify-client-secret-here"
SPOTIFY_REDIRECT_URI = "https://yourdomain.com/settings/music-services/spotify/callback"

# Spotify API Configuration
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

# Spotify Scopes Required
SPOTIFY_SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "playlist-read-private",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-library-read",
]

# ============================================================================
# Tidal Configuration
# ============================================================================
# Register your app at: https://developer.tidal.com

TIDAL_CLIENT_ID = "your-tidal-client-id-here"
TIDAL_CLIENT_SECRET = "your-tidal-client-secret-here"
TIDAL_REDIRECT_URI = "https://yourdomain.com/settings/music-services/tidal/callback"

# Tidal API Configuration
TIDAL_AUTH_URL = "https://auth.tidal.com/v1/oauth2/authorize"
TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_API_BASE_URL = "https://api.tidal.com/v1"

# Tidal Scopes Required
TIDAL_SCOPES = [
    "r_usr",  # Read user data
    "w_usr",  # Write user data
    "w_sub",  # Manage subscriptions
]

# ============================================================================
# YouTube Music Configuration (via Google OAuth)
# ============================================================================
# Register your app at: https://console.cloud.google.com
# Enable YouTube Data API v3

GOOGLE_CLIENT_ID = "your-google-client-id-here"
GOOGLE_CLIENT_SECRET = "your-google-client-secret-here"
YOUTUBE_MUSIC_REDIRECT_URI = "https://yourdomain.com/settings/music-services/youtube-music/callback"

# Google OAuth Configuration
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

# YouTube Music Scopes Required
YOUTUBE_MUSIC_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# ============================================================================
# Apple Music Configuration
# ============================================================================
# Register your app at: https://developer.apple.com/musickit
# Generate MusicKit identifier and keys

APPLE_TEAM_ID = "your-apple-team-id-here"
APPLE_KEY_ID = "your-apple-key-id-here"

# Apple Music Private Key (from .p8 file)
# DO NOT commit this to version control
APPLE_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgPaXyFvZfNydDEjxg
your-private-key-content-here
-----END PRIVATE KEY-----"""

# Apple Music API Configuration
APPLE_MUSIC_API_BASE_URL = "https://api.music.apple.com/v1"
APPLE_MUSIC_AUTH_URL = "https://appleid.apple.com/auth/authorize"

# Apple Music Token Configuration
APPLE_MUSIC_TOKEN_EXPIRY = 15777000  # 6 months in seconds
APPLE_MUSIC_KEY_ALGORITHM = "ES256"

# ============================================================================
# MusicMatch Feature Flags
# ============================================================================
# Enable/disable features for gradual rollout

MUSICMATCH_ENABLED = True
MUSICMATCH_GRAPH_ENABLED = True
MUSICMATCH_PLAYLIST_SYNC_ENABLED = True
MUSICMATCH_PLAYBACK_ENABLED = True
MUSICMATCH_DISCOVERY_ENABLED = False  # Not yet implemented

# ============================================================================
# MusicMatch Performance Settings
# ============================================================================

# Graph Generation
MUSICMATCH_GRAPH_MAX_NODES = 500
MUSICMATCH_GRAPH_MAX_EDGES = 1000
MUSICMATCH_GRAPH_CACHE_TTL = 3600  # 1 hour

# Playlist Sync
MUSICMATCH_SYNC_BATCH_SIZE = 100
MUSICMATCH_SYNC_MAX_RETRIES = 3
MUSICMATCH_SYNC_RETRY_DELAY = 5  # seconds

# Playback
MUSICMATCH_PLAYBACK_SESSION_TTL = 86400  # 24 hours
MUSICMATCH_PLAYBACK_QUEUE_MAX_SIZE = 1000

# Track Resolution
MUSICMATCH_TRACK_MAPPING_CACHE_TTL = 86400  # 24 hours
MUSICMATCH_TRACK_SEARCH_TIMEOUT = 10  # seconds

# ============================================================================
# Rate Limiting
# ============================================================================

MUSICMATCH_RATE_LIMIT = 100  # requests per minute
MUSICMATCH_RATE_LIMIT_BURST = 200  # burst allowance

# Service-specific rate limits (to avoid hitting external API limits)
SPOTIFY_API_RATE_LIMIT = 180  # requests per minute
TIDAL_API_RATE_LIMIT = 60  # requests per minute
YOUTUBE_API_RATE_LIMIT = 10000  # requests per day
APPLE_MUSIC_API_RATE_LIMIT = 1000  # requests per minute

# ============================================================================
# Caching Configuration
# ============================================================================

# Redis configuration for caching
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB_MUSICMATCH = 2  # Dedicated Redis DB for MusicMatch
REDIS_PASSWORD = None  # Set if Redis requires authentication

# Cache prefixes
MUSICMATCH_CACHE_PREFIX = "musicmatch:"
MUSICMATCH_GRAPH_CACHE_PREFIX = "musicmatch:graph:"
MUSICMATCH_TRACK_CACHE_PREFIX = "musicmatch:track:"
MUSICMATCH_PLAYBACK_CACHE_PREFIX = "musicmatch:playback:"

# ============================================================================
# Database Configuration
# ============================================================================

# PostgreSQL/TimescaleDB settings
# MusicMatch uses the main ListenBrainz database with a dedicated schema

# Connection pool settings
MUSICMATCH_DB_POOL_SIZE = 20
MUSICMATCH_DB_MAX_OVERFLOW = 10

# Query timeout (in seconds)
MUSICMATCH_DB_QUERY_TIMEOUT = 30

# ============================================================================
# Background Workers
# ============================================================================

# Token refresh worker
MUSICMATCH_TOKEN_REFRESH_INTERVAL = 3600  # Check every hour
MUSICMATCH_TOKEN_REFRESH_THRESHOLD = 300  # Refresh if < 5 minutes left

# Auto-sync worker
MUSICMATCH_AUTOSYNC_ENABLED = True
MUSICMATCH_AUTOSYNC_INTERVAL = 300  # Check every 5 minutes
MUSICMATCH_AUTOSYNC_BATCH_SIZE = 10  # Process 10 playlists per batch

# Graph generation worker
MUSICMATCH_GRAPH_GENERATION_ENABLED = True
MUSICMATCH_GRAPH_GENERATION_INTERVAL = 3600  # Generate every hour
MUSICMATCH_GRAPH_GENERATION_BATCH_SIZE = 100  # Process 100 users per batch

# ============================================================================
# Logging Configuration
# ============================================================================

MUSICMATCH_LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
MUSICMATCH_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MUSICMATCH_LOG_FILE = "/var/log/listenbrainz/musicmatch.log"

# Detailed logging for specific components
MUSICMATCH_LOG_OAUTH = True
MUSICMATCH_LOG_API_CALLS = True
MUSICMATCH_LOG_SYNC_OPERATIONS = True
MUSICMATCH_LOG_PLAYBACK = True

# ============================================================================
# Security Settings
# ============================================================================

# CORS settings for MusicMatch API
MUSICMATCH_CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]

# OAuth token encryption
MUSICMATCH_ENCRYPT_TOKENS = True
MUSICMATCH_ENCRYPTION_KEY = "your-32-byte-encryption-key-here"  # Generate securely!

# Session security
MUSICMATCH_SESSION_COOKIE_SECURE = True  # Require HTTPS
MUSICMATCH_SESSION_COOKIE_HTTPONLY = True
MUSICMATCH_SESSION_COOKIE_SAMESITE = "Lax"

# ============================================================================
# Monitoring & Analytics
# ============================================================================

# Sentry (error tracking)
MUSICMATCH_SENTRY_DSN = "https://your-sentry-dsn-here"
MUSICMATCH_SENTRY_ENVIRONMENT = "production"  # production, staging, development

# Metrics collection
MUSICMATCH_METRICS_ENABLED = True
MUSICMATCH_METRICS_ENDPOINT = "http://localhost:9090"  # Prometheus endpoint

# Analytics
MUSICMATCH_ANALYTICS_ENABLED = True
MUSICMATCH_ANALYTICS_SAMPLE_RATE = 0.1  # Sample 10% of events

# ============================================================================
# Development Settings
# ============================================================================

# Only use these in development environments

DEBUG_MUSICMATCH = False  # Set to True for verbose logging
MUSICMATCH_MOCK_EXTERNAL_APIS = False  # Set to True to mock service APIs
MUSICMATCH_SKIP_OAUTH_VERIFICATION = False  # NEVER set to True in production

# Test mode
MUSICMATCH_TEST_MODE = False  # Set to True when running tests

# ============================================================================
# Feature-Specific Settings
# ============================================================================

# Graph Visualization
MUSICMATCH_GRAPH_DEFAULT_LAYOUT = "force"  # force, circular, hierarchical, grid
MUSICMATCH_GRAPH_DEFAULT_TIME_RANGE = "month"  # week, month, year, all_time

# Playlist Sync
MUSICMATCH_SYNC_DEFAULT_FREQUENCY = 60  # minutes
MUSICMATCH_SYNC_AUTO_ENABLE = True  # Enable auto-sync by default

# Playback
MUSICMATCH_PLAYBACK_DEFAULT_SERVICE_PRIORITY = {
    "spotify": 4,
    "tidal": 3,
    "apple": 2,
    "youtube_music": 1,
}

# ============================================================================
# Internationalization
# ============================================================================

MUSICMATCH_SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "ja", "zh"]
MUSICMATCH_DEFAULT_LANGUAGE = "en"

# ============================================================================
# Notes
# ============================================================================

# 1. NEVER commit credentials to version control
# 2. Use environment variables for production secrets
# 3. Rotate API keys regularly
# 4. Monitor rate limits to avoid service disruption
# 5. Review security settings before production deployment
# 6. Keep this file in sync with deployment documentation
