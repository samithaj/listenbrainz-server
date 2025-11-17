import * as React from "react";
import { useState, useEffect, useCallback } from "react";
import { toast } from "react-toastify";

export interface PlaybackState {
  session: {
    session_id: string;
    service: string;
    started_at: string;
  } | null;
  playback_state: {
    is_playing: boolean;
    progress_ms: number;
    track_id: string;
    track_name: string;
    artist_name: string;
    duration_ms: number;
    device_name?: string;
    volume_percent?: number;
  } | null;
  queue: Array<{
    position: number;
    recording_mbid: string;
    added_at: string;
    played_at: string | null;
  }>;
  supports_server_control: boolean;
}

export interface UnifiedPlayerProps {
  onTrackChange?: (trackMbid: string) => void;
}

export default function UnifiedPlayer({ onTrackChange }: UnifiedPlayerProps) {
  const [playbackState, setPlaybackState] = useState<PlaybackState | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch playback status
  const fetchPlaybackStatus = useCallback(async () => {
    try {
      const response = await fetch("/1/musicmatch/playback/status", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch playback status");
      }

      const data = await response.json();
      setPlaybackState(data);
      setError(null);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to fetch status";
      setError(errorMsg);
      console.error(err);
    }
  }, []);

  // Poll for playback status
  useEffect(() => {
    fetchPlaybackStatus();

    const interval = setInterval(fetchPlaybackStatus, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [fetchPlaybackStatus]);

  const playTrack = async (recordingMbid: string, preferredService?: string) => {
    try {
      setLoading(true);
      const response = await fetch("/1/musicmatch/playback/play", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          recording_mbid: recordingMbid,
          preferred_service: preferredService,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start playback");
      }

      const data = await response.json();

      if (data.requires_client_sdk) {
        toast.info(
          `Playback requires ${data.service} client. Please use the ${data.service} app.`
        );
      } else {
        toast.success("Playback started");
      }

      fetchPlaybackStatus();

      if (onTrackChange) {
        onTrackChange(recordingMbid);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to play";
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const pausePlayback = async () => {
    try {
      const response = await fetch("/1/musicmatch/playback/pause", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to pause");
      }

      toast.success("Playback paused");
      fetchPlaybackStatus();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to pause";
      toast.error(errorMsg);
    }
  };

  const resumePlayback = async () => {
    try {
      const response = await fetch("/1/musicmatch/playback/resume", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to resume");
      }

      toast.success("Playback resumed");
      fetchPlaybackStatus();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to resume";
      toast.error(errorMsg);
    }
  };

  const skipTrack = async () => {
    try {
      const response = await fetch("/1/musicmatch/playback/skip", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to skip");
      }

      toast.success("Skipped to next track");
      fetchPlaybackStatus();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to skip";
      toast.error(errorMsg);
    }
  };

  const formatTime = (ms: number): string => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  const getServiceIcon = (service: string): string => {
    const icons: Record<string, string> = {
      spotify: "fa-spotify",
      tidal: "fa-music",
      youtube_music: "fa-youtube",
      apple: "fa-apple",
    };
    return icons[service] || "fa-music";
  };

  const getServiceName = (service: string): string => {
    const names: Record<string, string> = {
      spotify: "Spotify",
      tidal: "Tidal",
      youtube_music: "YouTube Music",
      apple: "Apple Music",
    };
    return names[service] || service;
  };

  if (error) {
    return (
      <div className="unified-player alert alert-danger">
        <i className="fa fa-exclamation-triangle" /> Error loading player: {error}
      </div>
    );
  }

  if (!playbackState || !playbackState.session) {
    return (
      <div className="unified-player">
        <div className="card">
          <div className="card-body text-center">
            <p className="text-muted">
              <i className="fa fa-music" /> No active playback session
            </p>
            <small className="text-muted">
              Click the play button on any track to start listening
            </small>
          </div>
        </div>
      </div>
    );
  }

  const { session, playback_state, supports_server_control, queue } =
    playbackState;

  return (
    <div className="unified-player">
      <div className="card">
        <div className="card-body">
          {/* Service indicator */}
          <div className="mb-3">
            <small className="text-muted">
              Playing on{" "}
              <i className={`fa ${getServiceIcon(session.service)} me-1`} />
              {getServiceName(session.service)}
            </small>
            {!supports_server_control && (
              <small className="text-warning ms-2">
                <i className="fa fa-info-circle" /> Requires client app
              </small>
            )}
          </div>

          {/* Now playing */}
          {playback_state && (
            <div className="now-playing mb-3">
              <h5 className="mb-1">{playback_state.track_name}</h5>
              <p className="text-muted mb-2">{playback_state.artist_name}</p>

              {/* Progress bar */}
              <div className="progress mb-2" style={{ height: "4px" }}>
                <div
                  className="progress-bar"
                  role="progressbar"
                  style={{
                    width: `${
                      (playback_state.progress_ms / playback_state.duration_ms) *
                      100
                    }%`,
                  }}
                />
              </div>

              <div className="d-flex justify-content-between">
                <small className="text-muted">
                  {formatTime(playback_state.progress_ms)}
                </small>
                <small className="text-muted">
                  {formatTime(playback_state.duration_ms)}
                </small>
              </div>
            </div>
          )}

          {/* Playback controls */}
          {supports_server_control && (
            <div className="playback-controls text-center mb-3">
              <div className="btn-group" role="group">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={skipTrack}
                  title="Skip to previous"
                  disabled={loading}
                >
                  <i className="fa fa-step-backward" />
                </button>

                {playback_state?.is_playing ? (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={pausePlayback}
                    disabled={loading}
                  >
                    <i className="fa fa-pause" />
                  </button>
                ) : (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={resumePlayback}
                    disabled={loading}
                  >
                    <i className="fa fa-play" />
                  </button>
                )}

                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={skipTrack}
                  title="Skip to next"
                  disabled={loading}
                >
                  <i className="fa fa-step-forward" />
                </button>
              </div>
            </div>
          )}

          {/* Queue info */}
          {queue && queue.length > 0 && (
            <div className="queue-info">
              <small className="text-muted">
                <i className="fa fa-list" /> {queue.length} tracks in queue
              </small>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
