import * as React from "react";
import { useState, useEffect } from "react";
import { toast } from "react-toastify";

export interface SyncSettings {
  auto_sync_enabled: boolean;
  sync_services: string[];
  sync_frequency_minutes: number;
}

export interface PlaylistSyncSettingsProps {
  playlistId: string;
  availableServices: string[];
  onSettingsUpdate?: (settings: SyncSettings) => void;
}

const SERVICE_LABELS: Record<string, string> = {
  spotify: "Spotify",
  tidal: "Tidal",
  youtube_music: "YouTube Music",
  apple: "Apple Music",
};

const FREQUENCY_OPTIONS = [
  { value: 15, label: "Every 15 minutes" },
  { value: 30, label: "Every 30 minutes" },
  { value: 60, label: "Every hour" },
  { value: 180, label: "Every 3 hours" },
  { value: 360, label: "Every 6 hours" },
  { value: 720, label: "Every 12 hours" },
  { value: 1440, label: "Once a day" },
];

export default function PlaylistSyncSettings({
  playlistId,
  availableServices,
  onSettingsUpdate,
}: PlaylistSyncSettingsProps) {
  const [settings, setSettings] = useState<SyncSettings>({
    auto_sync_enabled: true,
    sync_services: [],
    sync_frequency_minutes: 60,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, [playlistId]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/1/musicmatch/playlist/${playlistId}/sync-settings`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }

      const data = await response.json();
      setSettings(data.settings);
      setHasChanges(false);
    } catch (err) {
      toast.error("Failed to load sync settings");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      const response = await fetch(
        `/1/musicmatch/playlist/${playlistId}/sync-settings`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(settings),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to save settings: ${response.statusText}`);
      }

      toast.success("Sync settings saved successfully");
      setHasChanges(false);

      if (onSettingsUpdate) {
        onSettingsUpdate(settings);
      }
    } catch (err) {
      toast.error("Failed to save sync settings");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleAutoSyncToggle = (enabled: boolean) => {
    setSettings({ ...settings, auto_sync_enabled: enabled });
    setHasChanges(true);
  };

  const handleServiceToggle = (service: string) => {
    const newServices = settings.sync_services.includes(service)
      ? settings.sync_services.filter((s) => s !== service)
      : [...settings.sync_services, service];

    setSettings({ ...settings, sync_services: newServices });
    setHasChanges(true);
  };

  const handleFrequencyChange = (minutes: number) => {
    setSettings({ ...settings, sync_frequency_minutes: minutes });
    setHasChanges(true);
  };

  if (loading) {
    return (
      <div className="playlist-sync-settings">
        <div className="text-center">
          <i className="fa fa-spinner fa-spin" /> Loading settings...
        </div>
      </div>
    );
  }

  return (
    <div className="playlist-sync-settings">
      <div className="card">
        <div className="card-header">
          <h5 className="mb-0">
            <i className="fa fa-cog" /> Sync Settings
          </h5>
        </div>
        <div className="card-body">
          {/* Auto-sync toggle */}
          <div className="mb-4">
            <div className="form-check form-switch">
              <input
                className="form-check-input"
                type="checkbox"
                id="auto-sync-enabled"
                checked={settings.auto_sync_enabled}
                onChange={(e) => handleAutoSyncToggle(e.target.checked)}
              />
              <label className="form-check-label" htmlFor="auto-sync-enabled">
                <strong>Enable automatic synchronization</strong>
              </label>
            </div>
            <small className="text-muted">
              Automatically sync playlist changes to connected services
            </small>
          </div>

          {/* Service selection */}
          <div className="mb-4">
            <label className="form-label">
              <strong>Sync to these services:</strong>
            </label>
            <div className="row">
              {availableServices.map((service) => (
                <div key={service} className="col-md-6 mb-2">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id={`service-${service}`}
                      checked={settings.sync_services.includes(service)}
                      onChange={() => handleServiceToggle(service)}
                      disabled={!settings.auto_sync_enabled}
                    />
                    <label
                      className="form-check-label"
                      htmlFor={`service-${service}`}
                    >
                      {SERVICE_LABELS[service] || service}
                    </label>
                  </div>
                </div>
              ))}
            </div>
            {availableServices.length === 0 && (
              <div className="alert alert-info">
                <i className="fa fa-info-circle" /> Connect to music services in
                your{" "}
                <a href="/settings/music-services/details">
                  settings
                </a>{" "}
                to enable sync.
              </div>
            )}
          </div>

          {/* Sync frequency */}
          <div className="mb-4">
            <label htmlFor="sync-frequency" className="form-label">
              <strong>Sync frequency:</strong>
            </label>
            <select
              id="sync-frequency"
              className="form-select"
              value={settings.sync_frequency_minutes}
              onChange={(e) => handleFrequencyChange(Number(e.target.value))}
              disabled={!settings.auto_sync_enabled}
            >
              {FREQUENCY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <small className="text-muted">
              How often to check for changes and sync
            </small>
          </div>

          {/* Save button */}
          <div className="d-flex justify-content-end">
            <button
              type="button"
              className="btn btn-primary"
              onClick={saveSettings}
              disabled={!hasChanges || saving}
            >
              {saving ? (
                <>
                  <i className="fa fa-spinner fa-spin" /> Saving...
                </>
              ) : (
                <>
                  <i className="fa fa-save" /> Save Settings
                </>
              )}
            </button>
          </div>

          {/* Info box */}
          <div className="alert alert-info mt-3 mb-0">
            <strong>Note:</strong> Changes to your playlist will be
            automatically synced to selected services based on your frequency
            setting. You can also trigger a manual sync at any time.
          </div>
        </div>
      </div>
    </div>
  );
}
