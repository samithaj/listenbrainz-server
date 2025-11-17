import * as React from "react";
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { toast } from "react-toastify";
import { useCurrentUser } from "@/utils/GlobalAppContext";
import { UnifiedPlayer } from "../components";

interface ServiceStatus {
  service: string;
  connected: boolean;
  lastUsed?: string;
}

interface DashboardStats {
  total_plays: number;
  unique_tracks: number;
  services_used: number;
  total_duration_ms: number;
}

export default function Dashboard() {
  const { currentUser } = useCurrentUser();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch playback stats
      const statsResponse = await fetch("/1/musicmatch/playback/stats", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStats(data.stats);
      }

      // Determine connected services from user context
      const connectedServices: ServiceStatus[] = [];

      if (currentUser.spotifyAuth) {
        connectedServices.push({
          service: "spotify",
          connected: true,
        });
      }

      if (currentUser.tidalAuth) {
        connectedServices.push({
          service: "tidal",
          connected: true,
        });
      }

      if (currentUser.youtubeMusicAuth) {
        connectedServices.push({
          service: "youtube_music",
          connected: true,
        });
      }

      if (currentUser.appleAuth) {
        connectedServices.push({
          service: "apple",
          connected: true,
        });
      }

      setServices(connectedServices);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
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

  const formatDuration = (ms: number): string => {
    const hours = Math.floor(ms / 3600000);
    const minutes = Math.floor((ms % 3600000) / 60000);

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className="musicmatch-dashboard">
        <div className="container">
          <div className="text-center mt-5">
            <i className="fa fa-spinner fa-spin fa-3x" />
            <p className="mt-3">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="musicmatch-dashboard">
      <div className="container">
        {/* Header */}
        <div className="row mb-4">
          <div className="col-md-12">
            <h1>
              <i className="fa fa-music" /> MusicMatch Dashboard
            </h1>
            <p className="lead text-muted">
              Your unified music experience across all services
            </p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="row mb-4">
          <div className="col-md-3">
            <div className="card">
              <div className="card-body text-center">
                <h3 className="text-primary">
                  {stats?.total_plays.toLocaleString() || 0}
                </h3>
                <p className="text-muted mb-0">Total Plays</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card">
              <div className="card-body text-center">
                <h3 className="text-success">
                  {stats?.unique_tracks.toLocaleString() || 0}
                </h3>
                <p className="text-muted mb-0">Unique Tracks</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card">
              <div className="card-body text-center">
                <h3 className="text-info">{services.length}</h3>
                <p className="text-muted mb-0">Connected Services</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card">
              <div className="card-body text-center">
                <h3 className="text-warning">
                  {stats ? formatDuration(stats.total_duration_ms) : "0m"}
                </h3>
                <p className="text-muted mb-0">Listening Time</p>
              </div>
            </div>
          </div>
        </div>

        {/* Connected Services */}
        <div className="row mb-4">
          <div className="col-md-12">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">
                  <i className="fa fa-plug" /> Connected Services
                </h5>
              </div>
              <div className="card-body">
                {services.length === 0 ? (
                  <div className="alert alert-info">
                    <i className="fa fa-info-circle" /> You haven't connected
                    any music services yet.{" "}
                    <Link to="/settings/music-services/details">
                      Connect services
                    </Link>{" "}
                    to get started.
                  </div>
                ) : (
                  <div className="row">
                    {services.map((service) => (
                      <div key={service.service} className="col-md-3 mb-3">
                        <div className="card">
                          <div className="card-body text-center">
                            <i
                              className={`fa ${getServiceIcon(
                                service.service
                              )} fa-3x mb-2`}
                            />
                            <h6>{getServiceName(service.service)}</h6>
                            <span className="badge bg-success">Connected</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Unified Player */}
        <div className="row mb-4">
          <div className="col-md-12">
            <h5 className="mb-3">
              <i className="fa fa-play-circle" /> Now Playing
            </h5>
            <UnifiedPlayer />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="row mb-4">
          <div className="col-md-12">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">
                  <i className="fa fa-bolt" /> Quick Actions
                </h5>
              </div>
              <div className="card-body">
                <div className="row">
                  <div className="col-md-3">
                    <Link
                      to="/musicmatch/graph"
                      className="btn btn-outline-primary btn-block w-100"
                    >
                      <i className="fa fa-project-diagram" /> Explore Music
                      Graph
                    </Link>
                  </div>
                  <div className="col-md-3">
                    <Link
                      to="/musicmatch/playlists"
                      className="btn btn-outline-success btn-block w-100"
                    >
                      <i className="fa fa-list-ul" /> Manage Playlists
                    </Link>
                  </div>
                  <div className="col-md-3">
                    <Link
                      to="/musicmatch/discovery"
                      className="btn btn-outline-info btn-block w-100"
                    >
                      <i className="fa fa-compass" /> Discover Music
                    </Link>
                  </div>
                  <div className="col-md-3">
                    <Link
                      to="/settings/music-services/details"
                      className="btn btn-outline-warning btn-block w-100"
                    >
                      <i className="fa fa-cog" /> Manage Services
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Getting Started (if no services connected) */}
        {services.length === 0 && (
          <div className="row">
            <div className="col-md-12">
              <div className="card">
                <div className="card-header bg-primary text-white">
                  <h5 className="mb-0">
                    <i className="fa fa-rocket" /> Getting Started with
                    MusicMatch
                  </h5>
                </div>
                <div className="card-body">
                  <ol className="mb-0">
                    <li className="mb-2">
                      <strong>Connect your music services:</strong>{" "}
                      <Link to="/settings/music-services/details">
                        Go to settings
                      </Link>{" "}
                      and connect Spotify, Tidal, YouTube Music, or Apple Music
                    </li>
                    <li className="mb-2">
                      <strong>Explore your music graph:</strong> Visualize
                      relationships between your favorite artists, genres, and
                      tracks
                    </li>
                    <li className="mb-2">
                      <strong>Create unified playlists:</strong> Build playlists
                      once and sync them across all services
                    </li>
                    <li className="mb-0">
                      <strong>Enjoy seamless playback:</strong> Play music from
                      any service with intelligent track matching
                    </li>
                  </ol>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
