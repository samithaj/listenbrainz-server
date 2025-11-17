import * as React from "react";
import { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useCurrentUser } from "@/utils/GlobalAppContext";
import { PlaylistManager } from "../components";

interface Playlist {
  id: string;
  name: string;
  description?: string;
  trackCount: number;
  created: string;
}

export default function PlaylistManagerPage() {
  const { currentUser } = useCurrentUser();
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [selectedPlaylist, setSelectedPlaylist] = useState<Playlist | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [connectedServices, setConnectedServices] = useState<string[]>([]);

  useEffect(() => {
    fetchPlaylists();
    determineConnectedServices();
  }, []);

  const fetchPlaylists = async () => {
    try {
      setLoading(true);

      // Fetch user's playlists
      // Note: This endpoint would need to be created or use existing playlist API
      const response = await fetch(
        `/1/user/${currentUser.name}/playlists/collaborator`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        const data = await response.json();

        // Transform to our format
        const transformedPlaylists: Playlist[] = (data.playlists || []).map(
          (p: any) => ({
            id: p.identifier,
            name: p.playlist.title,
            description: p.playlist.annotation,
            trackCount: p.playlist.track ? p.playlist.track.length : 0,
            created: p.playlist.date || new Date().toISOString(),
          })
        );

        setPlaylists(transformedPlaylists);

        // Select first playlist by default
        if (transformedPlaylists.length > 0) {
          setSelectedPlaylist(transformedPlaylists[0]);
        }
      }
    } catch (err) {
      console.error("Error fetching playlists:", err);
      toast.error("Failed to load playlists");
    } finally {
      setLoading(false);
    }
  };

  const determineConnectedServices = () => {
    const services: string[] = [];

    if (currentUser.spotifyAuth) {
      services.push("spotify");
    }

    if (currentUser.tidalAuth) {
      services.push("tidal");
    }

    if (currentUser.youtubeMusicAuth) {
      services.push("youtube_music");
    }

    if (currentUser.appleAuth) {
      services.push("apple");
    }

    setConnectedServices(services);
  };

  if (loading) {
    return (
      <div className="playlist-manager-page">
        <div className="container">
          <div className="text-center mt-5">
            <i className="fa fa-spinner fa-spin fa-3x" />
            <p className="mt-3">Loading playlists...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="playlist-manager-page">
      <div className="container">
        {/* Header */}
        <div className="row mb-4">
          <div className="col-md-12">
            <h1>
              <i className="fa fa-list-ul" /> Playlist Management
            </h1>
            <p className="lead text-muted">
              Sync your playlists across all connected services
            </p>
          </div>
        </div>

        {/* No services warning */}
        {connectedServices.length === 0 && (
          <div className="row mb-4">
            <div className="col-md-12">
              <div className="alert alert-warning">
                <i className="fa fa-exclamation-triangle" /> You haven't
                connected any music services yet. To sync playlists,{" "}
                <a href="/settings/music-services/details">connect services</a>{" "}
                in your settings.
              </div>
            </div>
          </div>
        )}

        {/* Playlist List */}
        <div className="row mb-4">
          <div className="col-md-4">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Your Playlists</h5>
              </div>
              <div className="card-body p-0">
                {playlists.length === 0 ? (
                  <div className="p-3 text-center text-muted">
                    <i className="fa fa-info-circle" />
                    <p className="mb-0 mt-2">No playlists found</p>
                    <small>Create a playlist to get started</small>
                  </div>
                ) : (
                  <div className="list-group list-group-flush">
                    {playlists.map((playlist) => (
                      <button
                        key={playlist.id}
                        type="button"
                        className={`list-group-item list-group-item-action ${
                          selectedPlaylist?.id === playlist.id ? "active" : ""
                        }`}
                        onClick={() => setSelectedPlaylist(playlist)}
                      >
                        <div className="d-flex w-100 justify-content-between">
                          <h6 className="mb-1">{playlist.name}</h6>
                          <small>{playlist.trackCount} tracks</small>
                        </div>
                        {playlist.description && (
                          <small className="text-muted">
                            {playlist.description}
                          </small>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Playlist Manager */}
          <div className="col-md-8">
            {selectedPlaylist ? (
              <PlaylistManager
                playlistId={selectedPlaylist.id}
                playlistName={selectedPlaylist.name}
                userConnectedServices={connectedServices}
              />
            ) : (
              <div className="card">
                <div className="card-body text-center py-5">
                  <i className="fa fa-list-ul fa-3x text-muted" />
                  <p className="mt-3 text-muted">
                    Select a playlist to manage sync settings
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Info Cards */}
        <div className="row">
          <div className="col-md-6">
            <div className="card">
              <div className="card-header bg-info text-white">
                <h6 className="mb-0">
                  <i className="fa fa-info-circle" /> About Playlist Sync
                </h6>
              </div>
              <div className="card-body">
                <p>
                  Playlist synchronization allows you to create a playlist once
                  and sync it across all your connected music services.
                </p>
                <ul className="mb-0">
                  <li>Sync to multiple services simultaneously</li>
                  <li>Automatic or manual sync options</li>
                  <li>Track matching across services</li>
                  <li>Real-time sync status tracking</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="col-md-6">
            <div className="card">
              <div className="card-header bg-success text-white">
                <h6 className="mb-0">
                  <i className="fa fa-check-circle" /> Best Practices
                </h6>
              </div>
              <div className="card-body">
                <p>For the best playlist sync experience:</p>
                <ul className="mb-0">
                  <li>Connect multiple services for more flexibility</li>
                  <li>Use descriptive playlist names</li>
                  <li>Enable auto-sync for frequently updated playlists</li>
                  <li>Check sync status regularly for any issues</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
