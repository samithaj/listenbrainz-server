/**
 * @jest-environment jsdom
 */

import * as React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { toast } from "react-toastify";
import UnifiedPlayer from "../UnifiedPlayer";

// Mock react-toastify
jest.mock("react-toastify", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock fetch
global.fetch = jest.fn();

describe("UnifiedPlayer", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  it("renders no session state when no active playback", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: null,
        playback_state: null,
        queue: [],
        supports_server_control: false,
      }),
    });

    render(<UnifiedPlayer />);

    await waitFor(() => {
      expect(screen.getByText(/No active playback session/i)).toBeInTheDocument();
    });
  });

  it("renders playback state when session is active", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: "test-session",
          service: "spotify",
          started_at: "2025-11-17T10:00:00Z",
        },
        playback_state: {
          is_playing: true,
          progress_ms: 60000,
          track_id: "track-123",
          track_name: "Test Track",
          artist_name: "Test Artist",
          duration_ms: 180000,
        },
        queue: [],
        supports_server_control: true,
      }),
    });

    render(<UnifiedPlayer />);

    await waitFor(() => {
      expect(screen.getByText("Test Track")).toBeInTheDocument();
      expect(screen.getByText("Test Artist")).toBeInTheDocument();
      expect(screen.getByText(/Playing on/i)).toBeInTheDocument();
    });
  });

  it("shows play button when track is paused", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: "test-session",
          service: "spotify",
          started_at: "2025-11-17T10:00:00Z",
        },
        playback_state: {
          is_playing: false,
          progress_ms: 0,
          track_id: "track-123",
          track_name: "Test Track",
          artist_name: "Test Artist",
          duration_ms: 180000,
        },
        queue: [],
        supports_server_control: true,
      }),
    });

    render(<UnifiedPlayer />);

    await waitFor(() => {
      const playButton = screen.getByRole("button", { name: /fa-play/i });
      expect(playButton).toBeInTheDocument();
    });
  });

  it("shows pause button when track is playing", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: "test-session",
          service: "spotify",
          started_at: "2025-11-17T10:00:00Z",
        },
        playback_state: {
          is_playing: true,
          progress_ms: 60000,
          track_id: "track-123",
          track_name: "Test Track",
          artist_name: "Test Artist",
          duration_ms: 180000,
        },
        queue: [],
        supports_server_control: true,
      }),
    });

    render(<UnifiedPlayer />);

    await waitFor(() => {
      const pauseButton = screen.getByRole("button", { name: /fa-pause/i });
      expect(pauseButton).toBeInTheDocument();
    });
  });

  it("handles pause action", async () => {
    // Initial status response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: "test-session",
          service: "spotify",
          started_at: "2025-11-17T10:00:00Z",
        },
        playback_state: {
          is_playing: true,
          progress_ms: 60000,
          track_id: "track-123",
          track_name: "Test Track",
          artist_name: "Test Artist",
          duration_ms: 180000,
        },
        queue: [],
        supports_server_control: true,
      }),
    });

    render(<UnifiedPlayer />);

    await waitFor(() => {
      expect(screen.getByText("Test Track")).toBeInTheDocument();
    });

    // Mock pause response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    // Mock updated status response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: "test-session",
          service: "spotify",
          started_at: "2025-11-17T10:00:00Z",
        },
        playback_state: {
          is_playing: false,
          progress_ms: 60000,
          track_id: "track-123",
          track_name: "Test Track",
          artist_name: "Test Artist",
          duration_ms: 180000,
        },
        queue: [],
        supports_server_control: true,
      }),
    });

    const pauseButton = screen.getByRole("button", { name: /fa-pause/i });
    fireEvent.click(pauseButton);

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("Playback paused");
    });
  });

  it("shows client SDK warning for non-Spotify services", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: "test-session",
          service: "tidal",
          started_at: "2025-11-17T10:00:00Z",
        },
        playback_state: null,
        queue: [],
        supports_server_control: false,
      }),
    });

    render(<UnifiedPlayer />);

    await waitFor(() => {
      expect(screen.getByText(/Requires client app/i)).toBeInTheDocument();
    });
  });

  it("displays queue length", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: "test-session",
          service: "spotify",
          started_at: "2025-11-17T10:00:00Z",
        },
        playback_state: {
          is_playing: true,
          progress_ms: 0,
          track_id: "track-123",
          track_name: "Test Track",
          artist_name: "Test Artist",
          duration_ms: 180000,
        },
        queue: [
          { position: 0, recording_mbid: "mbid-1", added_at: "", played_at: null },
          { position: 1, recording_mbid: "mbid-2", added_at: "", played_at: null },
          { position: 2, recording_mbid: "mbid-3", added_at: "", played_at: null },
        ],
        supports_server_control: true,
      }),
    });

    render(<UnifiedPlayer />);

    await waitFor(() => {
      expect(screen.getByText(/3 tracks in queue/i)).toBeInTheDocument();
    });
  });

  it("handles fetch errors gracefully", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("Network error"));

    render(<UnifiedPlayer />);

    await waitFor(() => {
      expect(screen.getByText(/Error loading player/i)).toBeInTheDocument();
    });
  });

  it("formats time correctly", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: "test-session",
          service: "spotify",
          started_at: "2025-11-17T10:00:00Z",
        },
        playback_state: {
          is_playing: true,
          progress_ms: 125000, // 2:05
          track_id: "track-123",
          track_name: "Test Track",
          artist_name: "Test Artist",
          duration_ms: 305000, // 5:05
        },
        queue: [],
        supports_server_control: true,
      }),
    });

    render(<UnifiedPlayer />);

    await waitFor(() => {
      expect(screen.getByText("2:05")).toBeInTheDocument();
      expect(screen.getByText("5:05")).toBeInTheDocument();
    });
  });
});
