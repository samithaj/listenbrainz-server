"""
Unit tests for PlaylistSyncManager
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import uuid

from listenbrainz.background.playlist_sync.sync_manager import (
    PlaylistSyncManager,
    SyncStatus
)


class TestPlaylistSyncManager(unittest.TestCase):
    """Test PlaylistSyncManager functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 123
        self.playlist_id = str(uuid.uuid4())
        self.manager = PlaylistSyncManager(self.user_id, self.playlist_id)

    def test_initialization(self):
        """Test manager initialization"""
        self.assertEqual(self.manager.user_id, self.user_id)
        self.assertEqual(self.manager.playlist_id, self.playlist_id)

    @patch('listenbrainz.db.musicmatch.get_sync_mapping')
    def test_get_sync_status(self, mock_get_mapping):
        """Test getting sync status"""
        mock_get_mapping.return_value = [
            {
                'service': 'spotify',
                'external_playlist_id': 'spotify_id',
                'last_synced': '2025-11-17T10:00:00Z',
                'sync_status': 'completed',
                'error_message': None
            },
            {
                'service': 'tidal',
                'external_playlist_id': 'tidal_id',
                'last_synced': None,
                'sync_status': 'pending',
                'error_message': None
            }
        ]

        status = self.manager.get_sync_status()

        self.assertEqual(len(status), 2)
        self.assertEqual(status[0]['service'], 'spotify')
        self.assertEqual(status[0]['sync_status'], 'completed')
        self.assertEqual(status[1]['service'], 'tidal')
        self.assertEqual(status[1]['sync_status'], 'pending')

    @patch('listenbrainz.background.playlist_sync.spotify_sync.SpotifyPlaylistSync')
    @patch('listenbrainz.db.musicmatch.create_sync_job')
    @patch('listenbrainz.db.musicmatch.update_sync_mapping')
    def test_sync_to_services_success(
        self,
        mock_update_mapping,
        mock_create_job,
        mock_spotify_sync
    ):
        """Test successful sync to services"""
        # Mock Spotify sync
        mock_sync_instance = Mock()
        mock_sync_instance.create_playlist.return_value = {
            'playlist_id': 'spotify_playlist_id',
            'tracks_synced': 10,
            'tracks_failed': 0
        }
        mock_spotify_sync.return_value = mock_sync_instance

        # Mock job creation
        job_id = str(uuid.uuid4())
        mock_create_job.return_value = job_id

        playlist_data = {
            'name': 'Test Playlist',
            'description': 'Test Description',
            'tracks': [{'mbid': 'track-1'}, {'mbid': 'track-2'}]
        }

        result = self.manager.sync_to_services(
            services=['spotify'],
            playlist_data=playlist_data
        )

        self.assertEqual(result['job_id'], job_id)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['success_count'], 1)
        self.assertEqual(result['failure_count'], 0)

        mock_create_job.assert_called_once()
        mock_update_mapping.assert_called()

    @patch('listenbrainz.background.playlist_sync.spotify_sync.SpotifyPlaylistSync')
    def test_sync_to_services_failure(self, mock_spotify_sync):
        """Test sync failure handling"""
        # Mock Spotify sync to raise exception
        mock_sync_instance = Mock()
        mock_sync_instance.create_playlist.side_effect = Exception("Sync failed")
        mock_spotify_sync.return_value = mock_sync_instance

        playlist_data = {
            'name': 'Test Playlist',
            'tracks': []
        }

        result = self.manager.sync_to_services(
            services=['spotify'],
            playlist_data=playlist_data
        )

        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['success_count'], 0)
        self.assertEqual(result['failure_count'], 1)

    @patch('listenbrainz.db.musicmatch.get_sync_mapping')
    def test_needs_sync_never_synced(self, mock_get_mapping):
        """Test needs_sync for never synced playlist"""
        mock_get_mapping.return_value = []

        needs_sync = self.manager.needs_sync('spotify')

        self.assertTrue(needs_sync)

    @patch('listenbrainz.db.musicmatch.get_sync_mapping')
    def test_needs_sync_recently_synced(self, mock_get_mapping):
        """Test needs_sync for recently synced playlist"""
        from datetime import datetime, timedelta

        # Last synced 10 minutes ago
        last_synced = datetime.utcnow() - timedelta(minutes=10)

        mock_get_mapping.return_value = [{
            'service': 'spotify',
            'last_synced': last_synced.isoformat(),
            'sync_status': 'completed'
        }]

        needs_sync = self.manager.needs_sync('spotify', min_interval_minutes=60)

        self.assertFalse(needs_sync)

    @patch('listenbrainz.db.musicmatch.get_sync_mapping')
    def test_needs_sync_outdated(self, mock_get_mapping):
        """Test needs_sync for outdated playlist"""
        from datetime import datetime, timedelta

        # Last synced 2 hours ago
        last_synced = datetime.utcnow() - timedelta(hours=2)

        mock_get_mapping.return_value = [{
            'service': 'spotify',
            'last_synced': last_synced.isoformat(),
            'sync_status': 'completed'
        }]

        needs_sync = self.manager.needs_sync('spotify', min_interval_minutes=60)

        self.assertTrue(needs_sync)

    @patch('listenbrainz.db.musicmatch.get_sync_mapping')
    def test_needs_sync_failed_status(self, mock_get_mapping):
        """Test needs_sync for failed sync"""
        mock_get_mapping.return_value = [{
            'service': 'spotify',
            'last_synced': '2025-11-17T10:00:00Z',
            'sync_status': 'failed'
        }]

        needs_sync = self.manager.needs_sync('spotify')

        self.assertTrue(needs_sync)


if __name__ == '__main__':
    unittest.main()
