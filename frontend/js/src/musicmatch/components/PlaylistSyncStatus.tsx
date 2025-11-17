import * as React from "react";
import { useState, useEffect } from "react";
import { toast } from "react-toastify";

export interface SyncMapping {
  service: string;
  external_playlist_id: string;
  last_synced: string | null;
  sync_status: "pending" | "in_progress" | "completed" | "failed";
  error_message?: string;
}

export interface PlaylistSyncStatusProps {
  playlistId: string;
  onRefresh?: () => void;
}

export default function PlaylistSyncStatus({
  playlistId,
  onRefresh,
}: PlaylistSyncStatusProps) {
  const [syncMappings, setSyncMappings] = useState<SyncMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSyncStatus();
  }, [playlistId]);

  const fetchSyncStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/1/musicmatch/playlist/${playlistId}/sync-status`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch sync status: ${response.statusText}`);
      }

      const data = await response.json();
      setSyncMappings(data.mappings || []);
      setError(null);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to load sync status";
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeClass = (status: string): string => {
    switch (status) {
      case "completed":
        return "badge bg-success";
      case "in_progress":
        return "badge bg-info";
      case "pending":
        return "badge bg-warning";
      case "failed":
        return "badge bg-danger";
      default:
        return "badge bg-secondary";
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

  const formatLastSynced = (timestamp: string | null): string => {
    if (!timestamp) return "Never synced";
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const handleRefresh = () => {
    fetchSyncStatus();
    if (onRefresh) {
      onRefresh();
    }
  };

  if (loading) {
    return (
      <div className="playlist-sync-status">
        <div className="text-center">
          <i className="fa fa-spinner fa-spin" /> Loading sync status...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="playlist-sync-status">
        <div className="alert alert-danger">
          <i className="fa fa-exclamation-triangle" /> {error}
          <button
            type="button"
            className="btn btn-sm btn-outline-danger ms-2"
            onClick={handleRefresh}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (syncMappings.length === 0) {
    return (
      <div className="playlist-sync-status">
        <div className="alert alert-info">
          <i className="fa fa-info-circle" /> This playlist is not synced to any
          services yet.
        </div>
      </div>
    );
  }

  return (
    <div className="playlist-sync-status">
      <div className="d-flex justify-content-between align-items-center mb-2">
        <h5 className="mb-0">
          <i className="fa fa-sync-alt" /> Sync Status
        </h5>
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          onClick={handleRefresh}
          title="Refresh sync status"
        >
          <i className="fa fa-refresh" /> Refresh
        </button>
      </div>

      <div className="list-group">
        {syncMappings.map((mapping) => (
          <div
            key={mapping.service}
            className="list-group-item d-flex justify-content-between align-items-center"
          >
            <div className="d-flex align-items-center">
              <i
                className={`fa ${getServiceIcon(mapping.service)} fa-2x me-3`}
                style={{ width: "30px" }}
              />
              <div>
                <div className="fw-bold text-capitalize">
                  {mapping.service.replace("_", " ")}
                </div>
                <small className="text-muted">
                  {formatLastSynced(mapping.last_synced)}
                </small>
                {mapping.error_message && (
                  <div className="text-danger small">
                    <i className="fa fa-exclamation-circle" />{" "}
                    {mapping.error_message}
                  </div>
                )}
              </div>
            </div>
            <span className={getStatusBadgeClass(mapping.sync_status)}>
              {mapping.sync_status.replace("_", " ")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
