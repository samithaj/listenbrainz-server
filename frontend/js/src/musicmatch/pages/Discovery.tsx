import * as React from "react";
import { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useCurrentUser } from "@/utils/GlobalAppContext";

interface Track {
  recording_mbid?: string;
  track_name: string;
  artist_name: string;
  service: string;
}

interface Artist {
  artist_mbid?: string;
  artist_name: string;
  service: string;
}

export default function Discovery() {
  const { currentUser } = useCurrentUser();
  const [recommendedTracks, setRecommendedTracks] = useState<Track[]>([]);
  const [trendingArtists, setTrendingArtists] = useState<Artist[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"tracks" | "artists" | "genres">(
    "tracks"
  );

  useEffect(() => {
    fetchDiscoveryData();
  }, []);

  const fetchDiscoveryData = async () => {
    try {
      setLoading(true);

      // For now, we'll create placeholder data
      // In a real implementation, these would fetch from actual recommendation APIs

      // Simulated recommended tracks
      setRecommendedTracks([
        {
          track_name: "Example Track 1",
          artist_name: "Artist A",
          service: "spotify",
        },
        {
          track_name: "Example Track 2",
          artist_name: "Artist B",
          service: "tidal",
        },
        {
          track_name: "Example Track 3",
          artist_name: "Artist C",
          service: "apple",
        },
      ]);

      // Simulated trending artists
      setTrendingArtists([
        {
          artist_name: "Trending Artist 1",
          service: "spotify",
        },
        {
          artist_name: "Trending Artist 2",
          service: "youtube_music",
        },
        {
          artist_name: "Trending Artist 3",
          service: "apple",
        },
      ]);
    } catch (err) {
      console.error("Error fetching discovery data:", err);
      toast.error("Failed to load discovery content");
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

  if (loading) {
    return (
      <div className="discovery-page">
        <div className="container">
          <div className="text-center mt-5">
            <i className="fa fa-spinner fa-spin fa-3x" />
            <p className="mt-3">Loading discovery content...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="discovery-page">
      <div className="container">
        {/* Header */}
        <div className="row mb-4">
          <div className="col-md-12">
            <h1>
              <i className="fa fa-compass" /> Music Discovery
            </h1>
            <p className="lead text-muted">
              Explore recommendations from all your connected services
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="row mb-4">
          <div className="col-md-12">
            <ul className="nav nav-tabs" role="tablist">
              <li className="nav-item" role="presentation">
                <button
                  className={`nav-link ${
                    activeTab === "tracks" ? "active" : ""
                  }`}
                  onClick={() => setActiveTab("tracks")}
                  type="button"
                  role="tab"
                >
                  <i className="fa fa-music" /> Recommended Tracks
                </button>
              </li>
              <li className="nav-item" role="presentation">
                <button
                  className={`nav-link ${
                    activeTab === "artists" ? "active" : ""
                  }`}
                  onClick={() => setActiveTab("artists")}
                  type="button"
                  role="tab"
                >
                  <i className="fa fa-microphone" /> Trending Artists
                </button>
              </li>
              <li className="nav-item" role="presentation">
                <button
                  className={`nav-link ${
                    activeTab === "genres" ? "active" : ""
                  }`}
                  onClick={() => setActiveTab("genres")}
                  type="button"
                  role="tab"
                >
                  <i className="fa fa-tags" /> Genre Exploration
                </button>
              </li>
            </ul>
          </div>
        </div>

        {/* Tab Content */}
        <div className="row">
          <div className="col-md-12">
            {activeTab === "tracks" && (
              <div className="card">
                <div className="card-header">
                  <h5 className="mb-0">Recommended Tracks</h5>
                </div>
                <div className="card-body">
                  {recommendedTracks.length === 0 ? (
                    <div className="text-center py-5 text-muted">
                      <i className="fa fa-info-circle fa-2x" />
                      <p className="mt-3">
                        No recommendations available yet. Connect more services
                        and start listening to get personalized recommendations.
                      </p>
                    </div>
                  ) : (
                    <div className="list-group">
                      {recommendedTracks.map((track, index) => (
                        <div
                          key={index}
                          className="list-group-item list-group-item-action"
                        >
                          <div className="d-flex w-100 justify-content-between align-items-center">
                            <div>
                              <h6 className="mb-1">{track.track_name}</h6>
                              <small className="text-muted">
                                {track.artist_name}
                              </small>
                            </div>
                            <div className="text-end">
                              <small className="text-muted">
                                <i
                                  className={`fa ${getServiceIcon(
                                    track.service
                                  )} me-1`}
                                />
                                {getServiceName(track.service)}
                              </small>
                              <div className="mt-2">
                                <button
                                  type="button"
                                  className="btn btn-sm btn-primary me-1"
                                  title="Play"
                                >
                                  <i className="fa fa-play" />
                                </button>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-secondary"
                                  title="Add to queue"
                                >
                                  <i className="fa fa-plus" />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === "artists" && (
              <div className="card">
                <div className="card-header">
                  <h5 className="mb-0">Trending Artists</h5>
                </div>
                <div className="card-body">
                  {trendingArtists.length === 0 ? (
                    <div className="text-center py-5 text-muted">
                      <i className="fa fa-info-circle fa-2x" />
                      <p className="mt-3">
                        No trending artists available yet.
                      </p>
                    </div>
                  ) : (
                    <div className="row">
                      {trendingArtists.map((artist, index) => (
                        <div key={index} className="col-md-4 mb-3">
                          <div className="card h-100">
                            <div className="card-body text-center">
                              <i className="fa fa-user-circle fa-4x text-muted mb-3" />
                              <h6>{artist.artist_name}</h6>
                              <small className="text-muted">
                                <i
                                  className={`fa ${getServiceIcon(
                                    artist.service
                                  )} me-1`}
                                />
                                {getServiceName(artist.service)}
                              </small>
                              <div className="mt-3">
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-primary"
                                >
                                  <i className="fa fa-info-circle" /> View
                                  Details
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === "genres" && (
              <div className="card">
                <div className="card-header">
                  <h5 className="mb-0">Genre Exploration</h5>
                </div>
                <div className="card-body">
                  <div className="text-center py-5 text-muted">
                    <i className="fa fa-compass fa-2x" />
                    <p className="mt-3">
                      Genre exploration coming soon! Discover new music genres
                      based on your listening history.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="row mt-4">
          <div className="col-md-12">
            <div className="card bg-light">
              <div className="card-body">
                <h5>
                  <i className="fa fa-lightbulb" /> How Discovery Works
                </h5>
                <p className="mb-0">
                  MusicMatch aggregates recommendations from all your connected
                  music services to provide a unified discovery experience.
                  Connect more services to get better and more diverse
                  recommendations based on your listening habits across
                  platforms.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
