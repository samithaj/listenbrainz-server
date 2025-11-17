import * as React from "react";
import { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useCurrentUser } from "@/utils/GlobalAppContext";
import { MusicGraph, GraphControls, GraphData, LayoutType } from "../components";

type GraphType = "user" | "artist" | "genre";
type TimeRange = "week" | "month" | "year" | "all_time";

export default function GraphExplorer() {
  const { currentUser } = useCurrentUser();
  const [graphType, setGraphType] = useState<GraphType>("user");
  const [timeRange, setTimeRange] = useState<TimeRange>("month");
  const [layoutType, setLayoutType] = useState<LayoutType>("force");
  const [showLabels, setShowLabels] = useState(true);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [artistMbid, setArtistMbid] = useState("");
  const [genreName, setGenreName] = useState("");

  useEffect(() => {
    if (graphType === "user") {
      fetchUserGraph();
    }
  }, [graphType, timeRange]);

  const fetchUserGraph = async () => {
    try {
      setLoading(true);

      const response = await fetch(
        `/1/musicmatch/graph/user/${currentUser.name}?time_range=${timeRange}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch user graph");
      }

      const data = await response.json();
      setGraphData(data.graph);
    } catch (err) {
      console.error("Error fetching user graph:", err);
      toast.error("Failed to load music graph");
    } finally {
      setLoading(false);
    }
  };

  const fetchArtistGraph = async () => {
    if (!artistMbid.trim()) {
      toast.warn("Please enter an artist MBID");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(
        `/1/musicmatch/graph/artist/${artistMbid}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch artist graph");
      }

      const data = await response.json();
      setGraphData(data.graph);
    } catch (err) {
      console.error("Error fetching artist graph:", err);
      toast.error("Failed to load artist graph");
    } finally {
      setLoading(false);
    }
  };

  const fetchGenreGraph = async () => {
    if (!genreName.trim()) {
      toast.warn("Please enter a genre name");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(
        `/1/musicmatch/graph/genre?genre=${encodeURIComponent(genreName)}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch genre graph");
      }

      const data = await response.json();
      setGraphData(data.graph);
    } catch (err) {
      console.error("Error fetching genre graph:", err);
      toast.error("Failed to load genre graph");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    toast.info("Export functionality coming soon!");
  };

  const handleReset = () => {
    if (graphType === "user") {
      fetchUserGraph();
    }
  };

  return (
    <div className="graph-explorer">
      <div className="container-fluid">
        {/* Header */}
        <div className="row mb-4">
          <div className="col-md-12">
            <h1>
              <i className="fa fa-project-diagram" /> Music Graph Explorer
            </h1>
            <p className="lead text-muted">
              Visualize relationships between artists, genres, and tracks
            </p>
          </div>
        </div>

        {/* Graph Type Selection */}
        <div className="row mb-4">
          <div className="col-md-12">
            <div className="card">
              <div className="card-body">
                <h5 className="mb-3">Graph Type</h5>
                <div className="btn-group mb-3" role="group">
                  <button
                    type="button"
                    className={`btn ${
                      graphType === "user"
                        ? "btn-primary"
                        : "btn-outline-primary"
                    }`}
                    onClick={() => setGraphType("user")}
                  >
                    <i className="fa fa-user" /> My Music Graph
                  </button>
                  <button
                    type="button"
                    className={`btn ${
                      graphType === "artist"
                        ? "btn-primary"
                        : "btn-outline-primary"
                    }`}
                    onClick={() => setGraphType("artist")}
                  >
                    <i className="fa fa-microphone" /> Artist Relations
                  </button>
                  <button
                    type="button"
                    className={`btn ${
                      graphType === "genre"
                        ? "btn-primary"
                        : "btn-outline-primary"
                    }`}
                    onClick={() => setGraphType("genre")}
                  >
                    <i className="fa fa-tags" /> Genre Landscape
                  </button>
                </div>

                {/* User Graph Options */}
                {graphType === "user" && (
                  <div className="mt-3">
                    <label htmlFor="time-range" className="form-label">
                      <strong>Time Range:</strong>
                    </label>
                    <select
                      id="time-range"
                      className="form-select"
                      value={timeRange}
                      onChange={(e) => setTimeRange(e.target.value as TimeRange)}
                      style={{ maxWidth: "200px" }}
                    >
                      <option value="week">Last Week</option>
                      <option value="month">Last Month</option>
                      <option value="year">Last Year</option>
                      <option value="all_time">All Time</option>
                    </select>
                  </div>
                )}

                {/* Artist Graph Options */}
                {graphType === "artist" && (
                  <div className="mt-3">
                    <label htmlFor="artist-mbid" className="form-label">
                      <strong>Artist MusicBrainz ID:</strong>
                    </label>
                    <div className="input-group" style={{ maxWidth: "500px" }}>
                      <input
                        type="text"
                        id="artist-mbid"
                        className="form-control"
                        placeholder="e.g., 5b11f4ce-a62d-471e-81fc-a69a8278c7da"
                        value={artistMbid}
                        onChange={(e) => setArtistMbid(e.target.value)}
                      />
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={fetchArtistGraph}
                        disabled={loading}
                      >
                        <i className="fa fa-search" /> Load
                      </button>
                    </div>
                  </div>
                )}

                {/* Genre Graph Options */}
                {graphType === "genre" && (
                  <div className="mt-3">
                    <label htmlFor="genre-name" className="form-label">
                      <strong>Genre Name:</strong>
                    </label>
                    <div className="input-group" style={{ maxWidth: "500px" }}>
                      <input
                        type="text"
                        id="genre-name"
                        className="form-control"
                        placeholder="e.g., rock, jazz, electronic"
                        value={genreName}
                        onChange={(e) => setGenreName(e.target.value)}
                      />
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={fetchGenreGraph}
                        disabled={loading}
                      >
                        <i className="fa fa-search" /> Load
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Graph Controls */}
        {graphData && (
          <div className="row mb-4">
            <div className="col-md-12">
              <GraphControls
                layoutType={layoutType}
                showLabels={showLabels}
                onLayoutChange={setLayoutType}
                onShowLabelsChange={setShowLabels}
                onExport={handleExport}
                onReset={handleReset}
              />
            </div>
          </div>
        )}

        {/* Graph Visualization */}
        <div className="row mb-4">
          <div className="col-md-12">
            <div className="card">
              <div className="card-body">
                {loading && (
                  <div className="text-center py-5">
                    <i className="fa fa-spinner fa-spin fa-3x" />
                    <p className="mt-3">Loading graph...</p>
                  </div>
                )}

                {!loading && !graphData && (
                  <div className="text-center py-5">
                    <i className="fa fa-info-circle fa-3x text-muted" />
                    <p className="mt-3 text-muted">
                      {graphType === "user"
                        ? "Loading your music graph..."
                        : graphType === "artist"
                        ? "Enter an artist MBID to explore their relationships"
                        : "Enter a genre name to explore its landscape"}
                    </p>
                  </div>
                )}

                {!loading && graphData && (
                  <MusicGraph
                    data={graphData}
                    width={1200}
                    height={800}
                    layoutType={layoutType}
                    showLabels={showLabels}
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Graph Info */}
        {graphData && (
          <div className="row">
            <div className="col-md-12">
              <div className="card">
                <div className="card-body">
                  <h5 className="mb-3">Graph Statistics</h5>
                  <div className="row">
                    <div className="col-md-3">
                      <div className="text-center">
                        <h4>{graphData.nodes.length}</h4>
                        <p className="text-muted mb-0">Nodes</p>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="text-center">
                        <h4>{graphData.edges.length}</h4>
                        <p className="text-muted mb-0">Connections</p>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="text-center">
                        <h4>{layoutType}</h4>
                        <p className="text-muted mb-0">Layout</p>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="text-center">
                        <h4>{showLabels ? "Visible" : "Hidden"}</h4>
                        <p className="text-muted mb-0">Labels</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
