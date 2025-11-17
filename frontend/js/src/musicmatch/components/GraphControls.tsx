import * as React from "react";
import { LayoutType } from "./MusicGraph";

export interface GraphControlsProps {
  layoutType: LayoutType;
  showLabels: boolean;
  onLayoutChange: (layout: LayoutType) => void;
  onShowLabelsChange: (show: boolean) => void;
  onExport?: () => void;
  onReset?: () => void;
}

export default function GraphControls({
  layoutType,
  showLabels,
  onLayoutChange,
  onShowLabelsChange,
  onExport,
  onReset,
}: GraphControlsProps) {
  return (
    <div className="graph-controls" style={{ marginBottom: "20px" }}>
      <div className="card">
        <div className="card-body">
          <div className="row">
            {/* Layout Selection */}
            <div className="col-md-4">
              <label htmlFor="layout-select" className="form-label">
                <strong>Layout Algorithm</strong>
              </label>
              <select
                id="layout-select"
                className="form-control"
                value={layoutType}
                onChange={(e) => onLayoutChange(e.target.value as LayoutType)}
              >
                <option value="force">Force-Directed</option>
                <option value="circular">Circular</option>
                <option value="hierarchical">Hierarchical</option>
                <option value="grid">Grid</option>
              </select>
              <small className="form-text text-muted">
                Choose how nodes are arranged
              </small>
            </div>

            {/* Display Options */}
            <div className="col-md-4">
              <label className="form-label">
                <strong>Display Options</strong>
              </label>
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="show-labels"
                  checked={showLabels}
                  onChange={(e) => onShowLabelsChange(e.target.checked)}
                />
                <label className="form-check-label" htmlFor="show-labels">
                  Show node labels
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="col-md-4">
              <label className="form-label">
                <strong>Actions</strong>
              </label>
              <div className="btn-group" role="group">
                {onReset && (
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={onReset}
                    title="Reset graph to initial state"
                  >
                    <i className="fa fa-refresh" /> Reset
                  </button>
                )}
                {onExport && (
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-primary"
                    onClick={onExport}
                    title="Export graph as image"
                  >
                    <i className="fa fa-download" /> Export
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Layout Descriptions */}
          <div className="row mt-3">
            <div className="col-12">
              <small className="text-muted">
                {layoutType === "force" && (
                  <>
                    <strong>Force-Directed:</strong> Nodes are positioned based on
                    simulated physical forces. Connected nodes attract each other
                    while all nodes repel each other.
                  </>
                )}
                {layoutType === "circular" && (
                  <>
                    <strong>Circular:</strong> Nodes are arranged in a circle.
                    Good for visualizing cyclic relationships.
                  </>
                )}
                {layoutType === "hierarchical" && (
                  <>
                    <strong>Hierarchical:</strong> Nodes are arranged in levels
                    based on their connections. Good for tree-like structures.
                  </>
                )}
                {layoutType === "grid" && (
                  <>
                    <strong>Grid:</strong> Nodes are arranged in a regular grid
                    pattern. Good for systematic comparison.
                  </>
                )}
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
