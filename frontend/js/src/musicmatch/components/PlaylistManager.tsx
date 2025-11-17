import * as React from "react";
import { useState, useEffect } from "react";
import { toast } from "react-toastify";
import PlaylistSyncStatus from "./PlaylistSyncStatus";
import PlaylistSyncSettings from "./PlaylistSyncSettings";

export interface PlaylistManagerProps {
  playlistId: string;
  playlistName: string;
  userConnectedServices: string[];
}

interface SyncJob {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  services: string[];
  success_count: number;
  failure_count: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export default function PlaylistManager({
  playlistId,
  playlistName,
  userConnectedServices,
}: PlaylistManagerProps) {
  const [activeTab, setActiveTab] = useState<"status" | "settings">("status");
  const [syncing, setSyncing] = useState(false);
  const [currentJob, setCurrentJob] = useState<SyncJob | null>(null);
  const [selectedServices, setSelectedServices] = useState<string[]>([]);

  useEffect(() => {
    // Initialize with all connected services selected
    setSelectedServices(userConnectedServices);
  }, [userConnectedServices]);

  const triggerSync = async (force: boolean = false) => {
    if (selectedServices.length === 0) {
      toast.warn("Please select at least one service to sync");
      return;
    }

    try {
      setSyncing(true);
      const response = await fetch(
        `/1/musicmatch/playlist/${playlistId}/sync`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            services: selectedServices,
            force,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to trigger sync: ${response.statusText}`);
      }

      const data = await response.json();
      setCurrentJob(data.job);
      toast.success("Sync started successfully");

      // Poll for job status
      if (data.job.job_id) {
        pollJobStatus(data.job.job_id);
      }
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to trigger sync";
      toast.error(errorMsg);
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/1/musicmatch/playlist/jobs/${jobId}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch job status");
        }

        const data = await response.json();
        const job = data.job;
        setCurrentJob(job);

        // Stop polling when job is complete or failed
        if (job.status === "completed" || job.status === "failed") {
          clearInterval(pollInterval);

          if (job.status === "completed") {
            toast.success(
              `Sync completed! ${job.success_count} service(s) synced successfully`
            );
          } else {
            toast.error(`Sync failed: ${job.error_message || "Unknown error"}`);
          }
        }
      } catch (err) {
        console.error("Error polling job status:", err);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  const handleServiceToggle = (service: string) => {
    setSelectedServices((prev) =>
      prev.includes(service)
        ? prev.filter((s) => s !== service)
        : [...prev, service]
    );
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

  const getServiceLabel = (service: string): string => {
    const labels: Record<string, string> = {
      spotify: "Spotify",
      tidal: "Tidal",
      youtube_music: "YouTube Music",
      apple: "Apple Music",
    };
    return labels[service] || service;
  };

  return (
    <div className="playlist-manager">
      <div className="card">
        <div className="card-header">
          <h4 className="mb-0">
            <i className="fa fa-list-ul" /> {playlistName}
          </h4>
          <small className="text-muted">Unified Playlist Management</small>
        </div>
        <div className="card-body">
          {/* Sync Controls */}
          <div className="mb-4">
            <h5>
              <i className="fa fa-sync-alt" /> Sync to Services
            </h5>

            {userConnectedServices.length === 0 ? (
              <div className="alert alert-warning">
                <i className="fa fa-exclamation-triangle" /> You haven't
                connected any music services yet.{" "}
                <a href="/settings/music-services/details">
                  Connect services
                </a>{" "}
                to enable playlist sync.
              </div>
            ) : (
              <>
                <div className="row mb-3">
                  {userConnectedServices.map((service) => (
                    <div key={service} className="col-md-3 mb-2">
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id={`sync-${service}`}
                          checked={selectedServices.includes(service)}
                          onChange={() => handleServiceToggle(service)}
                          disabled={syncing}
                        />
                        <label
                          className="form-check-label"
                          htmlFor={`sync-${service}`}
                        >
                          <i className={`fa ${getServiceIcon(service)} me-1`} />
                          {getServiceLabel(service)}
                        </label>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="btn-group" role="group">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => triggerSync(false)}
                    disabled={syncing || selectedServices.length === 0}
                  >
                    {syncing ? (
                      <>
                        <i className="fa fa-spinner fa-spin" /> Syncing...
                      </>
                    ) : (
                      <>
                        <i className="fa fa-sync" /> Sync Now
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-primary"
                    onClick={() => triggerSync(true)}
                    disabled={syncing || selectedServices.length === 0}
                    title="Force sync even if playlist hasn't changed"
                  >
                    <i className="fa fa-sync-alt" /> Force Sync
                  </button>
                </div>
              </>
            )}

            {/* Current Job Status */}
            {currentJob && (
              <div className="mt-3">
                <div className="alert alert-info">
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <strong>Current Sync Job:</strong>
                      <div className="small">
                        Status: <span className="text-capitalize">{currentJob.status}</span>
                        {currentJob.status === "running" && (
                          <i className="fa fa-spinner fa-spin ms-2" />
                        )}
                      </div>
                      {currentJob.status === "completed" && (
                        <div className="small text-success">
                          <i className="fa fa-check-circle" /> Successfully
                          synced to {currentJob.success_count} service(s)
                        </div>
                      )}
                      {currentJob.status === "failed" && (
                        <div className="small text-danger">
                          <i className="fa fa-exclamation-circle" />{" "}
                          {currentJob.error_message}
                        </div>
                      )}
                    </div>
                    <div className="text-end">
                      <small className="text-muted">
                        Services: {currentJob.services.join(", ")}
                      </small>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Tabs */}
          <ul className="nav nav-tabs mb-3" role="tablist">
            <li className="nav-item" role="presentation">
              <button
                className={`nav-link ${activeTab === "status" ? "active" : ""}`}
                onClick={() => setActiveTab("status")}
                type="button"
                role="tab"
              >
                <i className="fa fa-info-circle" /> Sync Status
              </button>
            </li>
            <li className="nav-item" role="presentation">
              <button
                className={`nav-link ${
                  activeTab === "settings" ? "active" : ""
                }`}
                onClick={() => setActiveTab("settings")}
                type="button"
                role="tab"
              >
                <i className="fa fa-cog" /> Settings
              </button>
            </li>
          </ul>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === "status" && (
              <div className="tab-pane fade show active">
                <PlaylistSyncStatus
                  playlistId={playlistId}
                  onRefresh={() => {
                    // Optionally refresh other data
                  }}
                />
              </div>
            )}
            {activeTab === "settings" && (
              <div className="tab-pane fade show active">
                <PlaylistSyncSettings
                  playlistId={playlistId}
                  availableServices={userConnectedServices}
                  onSettingsUpdate={(settings) => {
                    toast.info("Settings updated");
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
