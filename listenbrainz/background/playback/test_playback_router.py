"""
Unit tests for PlaybackRouter
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import uuid

from listenbrainz.background.playback.playback_router import (
    PlaybackRouter,
    PlaybackState
)
from data.model.external_service import ExternalServiceType


class TestPlaybackRouter(unittest.TestCase):
    """Test PlaybackRouter functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 123
        self.router = PlaybackRouter(self.user_id)

    def test_initialization(self):
        """Test router initialization"""
        self.assertEqual(self.router.user_id, self.user_id)
        self.assertIsNone(self.router.current_session_id)
        self.assertIsNone(self.router.current_service)
        self.assertEqual(self.router.current_state, PlaybackState.STOPPED)
        self.assertIsNone(self.router.current_track)
        self.assertEqual(self.router.queue, [])

    def test_service_priority(self):
        """Test service priority ordering"""
        # Spotify should have highest priority
        self.assertEqual(
            self.router.service_priority[ExternalServiceType.SPOTIFY],
            4
        )
        # Tidal should have second highest
        self.assertEqual(
            self.router.service_priority[ExternalServiceType.TIDAL],
            3
        )

    @patch('listenbrainz.db.external_service_oauth.get_token')
    def test_get_user_connected_services(self, mock_get_token):
        """Test getting connected services"""
        # Mock token responses
        def token_side_effect(user_id, service_type):
            if service_type == ExternalServiceType.SPOTIFY:
                return {"access_token": "spotify_token"}
            elif service_type == ExternalServiceType.TIDAL:
                return {"access_token": "tidal_token"}
            return None

        mock_get_token.side_effect = token_side_effect

        services = self.router.get_user_connected_services()

        self.assertIn("spotify", services)
        self.assertIn("tidal", services)
        self.assertNotIn("apple", services)
        self.assertNotIn("youtube_music", services)

    def test_select_playback_service_with_preference(self):
        """Test service selection with user preference"""
        available_services = {
            "spotify": "spotify_track_id",
            "tidal": "tidal_track_id"
        }

        with patch.object(
            self.router,
            'get_user_connected_services',
            return_value=["spotify", "tidal"]
        ):
            service, track_id = self.router.select_playback_service(
                recording_mbid="test-mbid",
                available_services=available_services,
                preferred_service="tidal"
            )

            self.assertEqual(service, "tidal")
            self.assertEqual(track_id, "tidal_track_id")

    def test_select_playback_service_by_priority(self):
        """Test service selection by priority"""
        available_services = {
            "youtube_music": "yt_track_id",
            "spotify": "spotify_track_id",
            "tidal": "tidal_track_id"
        }

        with patch.object(
            self.router,
            'get_user_connected_services',
            return_value=["youtube_music", "spotify", "tidal"]
        ):
            service, track_id = self.router.select_playback_service(
                recording_mbid="test-mbid",
                available_services=available_services
            )

            # Should select Spotify (highest priority)
            self.assertEqual(service, "spotify")
            self.assertEqual(track_id, "spotify_track_id")

    def test_select_playback_service_no_available(self):
        """Test service selection with no available services"""
        with patch.object(
            self.router,
            'get_user_connected_services',
            return_value=[]
        ):
            service, track_id = self.router.select_playback_service(
                recording_mbid="test-mbid",
                available_services={}
            )

            self.assertIsNone(service)
            self.assertIsNone(track_id)

    @patch('listenbrainz.db.musicmatch.create_playback_session')
    def test_create_session(self, mock_create_session):
        """Test session creation"""
        session_id = self.router.create_session("spotify")

        self.assertIsNotNone(session_id)
        self.assertEqual(self.router.current_session_id, session_id)
        self.assertEqual(self.router.current_service, "spotify")

        # Verify database call
        mock_create_session.assert_called_once()
        call_args = mock_create_session.call_args[1]
        self.assertEqual(call_args['user_id'], self.user_id)
        self.assertEqual(call_args['service'], "spotify")

    @patch('listenbrainz.db.musicmatch.end_playback_session')
    def test_end_session(self, mock_end_session):
        """Test session ending"""
        # Create a session first
        self.router.current_session_id = str(uuid.uuid4())
        self.router.current_service = "spotify"
        self.router.current_state = PlaybackState.PLAYING

        self.router.end_session()

        self.assertIsNone(self.router.current_session_id)
        self.assertIsNone(self.router.current_service)
        self.assertEqual(self.router.current_state, PlaybackState.STOPPED)
        self.assertIsNone(self.router.current_track)

        mock_end_session.assert_called_once()

    def test_add_to_queue(self):
        """Test adding tracks to queue"""
        mbid1 = "mbid-1"
        mbid2 = "mbid-2"

        self.router.add_to_queue(mbid1)
        self.router.add_to_queue(mbid2)

        self.assertEqual(len(self.router.queue), 2)
        self.assertEqual(self.router.queue[0], mbid1)
        self.assertEqual(self.router.queue[1], mbid2)

    def test_add_to_queue_at_position(self):
        """Test adding track at specific position"""
        self.router.add_to_queue("mbid-1")
        self.router.add_to_queue("mbid-2")
        self.router.add_to_queue("mbid-3", position=1)

        self.assertEqual(self.router.queue[0], "mbid-1")
        self.assertEqual(self.router.queue[1], "mbid-3")
        self.assertEqual(self.router.queue[2], "mbid-2")

    def test_get_queue(self):
        """Test getting queue"""
        self.router.queue = ["mbid-1", "mbid-2"]
        queue = self.router.get_queue()

        self.assertEqual(queue, ["mbid-1", "mbid-2"])
        # Should return a copy
        queue.append("mbid-3")
        self.assertEqual(len(self.router.queue), 2)

    def test_clear_queue(self):
        """Test clearing queue"""
        self.router.queue = ["mbid-1", "mbid-2"]
        self.router.clear_queue()

        self.assertEqual(self.router.queue, [])

    def test_get_next_track(self):
        """Test getting next track from queue"""
        self.router.queue = ["mbid-1", "mbid-2", "mbid-3"]

        next_track = self.router.get_next_track()
        self.assertEqual(next_track, "mbid-1")
        self.assertEqual(len(self.router.queue), 2)

        next_track = self.router.get_next_track()
        self.assertEqual(next_track, "mbid-2")
        self.assertEqual(len(self.router.queue), 1)

    def test_get_next_track_empty_queue(self):
        """Test getting next track from empty queue"""
        next_track = self.router.get_next_track()
        self.assertIsNone(next_track)

    @patch.object(PlaybackRouter, 'end_session')
    @patch.object(PlaybackRouter, 'create_session')
    @patch.object(PlaybackRouter, 'get_user_connected_services')
    def test_switch_service(self, mock_get_services, mock_create, mock_end):
        """Test switching between services"""
        mock_get_services.return_value = ["spotify", "tidal"]
        mock_create.return_value = "new-session-id"

        self.router.current_session_id = "old-session-id"
        self.router.current_service = "spotify"

        success = self.router.switch_service("tidal")

        self.assertTrue(success)
        mock_end.assert_called_once()
        mock_create.assert_called_once_with("tidal")

    @patch.object(PlaybackRouter, 'get_user_connected_services')
    def test_switch_service_not_connected(self, mock_get_services):
        """Test switching to service not connected"""
        mock_get_services.return_value = ["spotify"]

        success = self.router.switch_service("tidal")

        self.assertFalse(success)

    def test_get_playback_info(self):
        """Test getting playback info"""
        self.router.current_session_id = "session-123"
        self.router.current_service = "spotify"
        self.router.current_state = PlaybackState.PLAYING
        self.router.current_track = "track-mbid"
        self.router.queue = ["mbid-1", "mbid-2"]

        info = self.router.get_playback_info()

        self.assertEqual(info['session_id'], "session-123")
        self.assertEqual(info['service'], "spotify")
        self.assertEqual(info['state'], "playing")
        self.assertEqual(info['current_track'], "track-mbid")
        self.assertEqual(info['queue_length'], 2)
        self.assertEqual(info['queue'], ["mbid-1", "mbid-2"])

    def test_set_playback_state(self):
        """Test setting playback state"""
        self.router.set_playback_state(PlaybackState.PLAYING, "track-mbid")

        self.assertEqual(self.router.current_state, PlaybackState.PLAYING)
        self.assertEqual(self.router.current_track, "track-mbid")


if __name__ == '__main__':
    unittest.main()
