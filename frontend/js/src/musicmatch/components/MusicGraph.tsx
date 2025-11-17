import * as React from "react";
import { toast } from "react-toastify";
import { ToastMsg } from "../../notifications/Notifications";
import {
  GraphData,
  GraphNode,
  GraphEdge,
  LayoutConfig,
  ForceDirectedLayout,
  circularLayout,
  hierarchicalLayout,
  gridLayout,
  getNodeColor,
  getEdgeColor,
} from "../utils/graphLayout";

export type LayoutType = "force" | "circular" | "hierarchical" | "grid";

export interface MusicGraphProps {
  graphData: GraphData;
  width?: number;
  height?: number;
  layoutType?: LayoutType;
  onNodeClick?: (node: GraphNode) => void;
  onNodeHover?: (node: GraphNode | null) => void;
  showLabels?: boolean;
  interactive?: boolean;
}

interface MusicGraphState {
  layoutData: GraphData;
  hoveredNode: GraphNode | null;
  selectedNode: GraphNode | null;
  isDragging: boolean;
  draggedNode: GraphNode | null;
}

export default class MusicGraph extends React.Component<
  MusicGraphProps,
  MusicGraphState
> {
  private canvasRef: React.RefObject<HTMLCanvasElement>;
  private containerRef: React.RefObject<HTMLDivElement>;
  private forceLayout: ForceDirectedLayout | null = null;
  private animationFrame: number | null = null;

  constructor(props: MusicGraphProps) {
    super(props);

    this.canvasRef = React.createRef();
    this.containerRef = React.createRef();

    this.state = {
      layoutData: props.graphData,
      hoveredNode: null,
      selectedNode: null,
      isDragging: false,
      draggedNode: null,
    };
  }

  componentDidMount() {
    this.applyLayout();
    this.draw();

    // Add event listeners
    const canvas = this.canvasRef.current;
    if (canvas && this.props.interactive !== false) {
      canvas.addEventListener("mousemove", this.handleMouseMove);
      canvas.addEventListener("mousedown", this.handleMouseDown);
      canvas.addEventListener("mouseup", this.handleMouseUp);
      canvas.addEventListener("click", this.handleClick);
    }
  }

  componentDidUpdate(prevProps: MusicGraphProps) {
    if (
      prevProps.graphData !== this.props.graphData ||
      prevProps.layoutType !== this.props.layoutType
    ) {
      this.applyLayout();
    }
    this.draw();
  }

  componentWillUnmount() {
    const canvas = this.canvasRef.current;
    if (canvas) {
      canvas.removeEventListener("mousemove", this.handleMouseMove);
      canvas.removeEventListener("mousedown", this.handleMouseDown);
      canvas.removeEventListener("mouseup", this.handleMouseUp);
      canvas.removeEventListener("click", this.handleClick);
    }

    if (this.forceLayout) {
      this.forceLayout.stop();
    }

    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
  }

  applyLayout = () => {
    const { graphData, layoutType = "force", width = 800, height = 600 } = this.props;

    const config: LayoutConfig = {
      width,
      height,
      nodeRadius: 8,
      linkDistance: 100,
      chargeStrength: -200,
    };

    let layoutData: GraphData;

    switch (layoutType) {
      case "circular":
        layoutData = circularLayout(graphData, config);
        break;
      case "hierarchical":
        layoutData = hierarchicalLayout(graphData, config);
        break;
      case "grid":
        layoutData = gridLayout(graphData, config);
        break;
      case "force":
      default:
        // For force layout, start simulation
        if (this.forceLayout) {
          this.forceLayout.stop();
        }

        this.forceLayout = new ForceDirectedLayout(graphData, config);
        this.forceLayout.start((data) => {
          this.setState({ layoutData: data });
        }, 300);

        layoutData = graphData;
        break;
    }

    this.setState({ layoutData });
  };

  handleMouseMove = (event: MouseEvent) => {
    const { interactive = true } = this.props;
    if (!interactive) return;

    const canvas = this.canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    if (this.state.isDragging && this.state.draggedNode && this.forceLayout) {
      // Update dragged node position
      this.forceLayout.fixNode(this.state.draggedNode.id, x, y);
      return;
    }

    // Check if hovering over a node
    const hoveredNode = this.getNodeAtPosition(x, y);

    if (hoveredNode !== this.state.hoveredNode) {
      this.setState({ hoveredNode });
      this.props.onNodeHover?.(hoveredNode);

      // Change cursor
      canvas.style.cursor = hoveredNode ? "pointer" : "default";
    }
  };

  handleMouseDown = (event: MouseEvent) => {
    const { interactive = true } = this.props;
    if (!interactive) return;

    const canvas = this.canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const node = this.getNodeAtPosition(x, y);

    if (node) {
      this.setState({
        isDragging: true,
        draggedNode: node,
      });
    }
  };

  handleMouseUp = () => {
    if (this.state.draggedNode && this.forceLayout) {
      this.forceLayout.releaseNode(this.state.draggedNode.id);
    }

    this.setState({
      isDragging: false,
      draggedNode: null,
    });
  };

  handleClick = (event: MouseEvent) => {
    const { interactive = true } = this.props;
    if (!interactive) return;

    const canvas = this.canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const node = this.getNodeAtPosition(x, y);

    if (node) {
      this.setState({ selectedNode: node });
      this.props.onNodeClick?.(node);
    } else {
      this.setState({ selectedNode: null });
    }
  };

  getNodeAtPosition(x: number, y: number): GraphNode | null {
    const { layoutData } = this.state;
    const nodeRadius = 8;

    for (const node of layoutData.nodes) {
      if (!node.x || !node.y) continue;

      const dx = x - node.x;
      const dy = y - node.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance <= nodeRadius * 1.5) {
        return node;
      }
    }

    return null;
  }

  draw = () => {
    const canvas = this.canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { width = 800, height = 600, showLabels = true } = this.props;
    const { layoutData, hoveredNode, selectedNode } = this.state;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw edges
    layoutData.edges.forEach((edge) => {
      const source =
        typeof edge.source === "string"
          ? layoutData.nodes.find((n) => n.id === edge.source)
          : edge.source;

      const target =
        typeof edge.target === "string"
          ? layoutData.nodes.find((n) => n.id === edge.target)
          : edge.target;

      if (!source || !target || !source.x || !source.y || !target.x || !target.y) {
        return;
      }

      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.strokeStyle = getEdgeColor(edge.type);
      ctx.lineWidth = Math.min((edge.weight || 1) * 2, 3);
      ctx.globalAlpha = 0.6;
      ctx.stroke();
      ctx.globalAlpha = 1;
    });

    // Draw nodes
    layoutData.nodes.forEach((node) => {
      if (!node.x || !node.y) return;

      const isHovered = hoveredNode?.id === node.id;
      const isSelected = selectedNode?.id === node.id;
      const radius = isHovered || isSelected ? 12 : 8;

      // Draw node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = getNodeColor(node.type);
      ctx.fill();

      // Draw border for selected/hovered nodes
      if (isHovered || isSelected) {
        ctx.strokeStyle = isSelected ? "#FFD700" : "#FFF";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Draw label
      if (showLabels && (isHovered || isSelected || layoutData.nodes.length < 30)) {
        ctx.font = isHovered || isSelected ? "bold 12px sans-serif" : "10px sans-serif";
        ctx.fillStyle = "#333";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(node.label, node.x, node.y + radius + 4);
      }
    });

    // Request next frame for animation
    if (this.forceLayout && this.props.layoutType === "force") {
      this.animationFrame = requestAnimationFrame(this.draw);
    }
  };

  render() {
    const { width = 800, height = 600 } = this.props;
    const { hoveredNode, selectedNode } = this.state;

    return (
      <div ref={this.containerRef} className="music-graph-container">
        <canvas
          ref={this.canvasRef}
          width={width}
          height={height}
          style={{
            border: "1px solid #ddd",
            borderRadius: "8px",
            backgroundColor: "#fafafa",
          }}
        />

        {(hoveredNode || selectedNode) && (
          <div
            className="graph-node-tooltip"
            style={{
              position: "absolute",
              top: "10px",
              right: "10px",
              padding: "10px",
              backgroundColor: "white",
              border: "1px solid #ddd",
              borderRadius: "4px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
              maxWidth: "250px",
            }}
          >
            <div style={{ fontWeight: "bold", marginBottom: "5px" }}>
              {(selectedNode || hoveredNode)!.label}
            </div>
            <div style={{ fontSize: "12px", color: "#666" }}>
              Type: {(selectedNode || hoveredNode)!.type}
            </div>
            {(selectedNode || hoveredNode)!.weight && (
              <div style={{ fontSize: "12px", color: "#666" }}>
                Weight: {(selectedNode || hoveredNode)!.weight}
              </div>
            )}
            {(selectedNode || hoveredNode)!.metadata && (
              <div style={{ fontSize: "11px", color: "#888", marginTop: "5px" }}>
                {JSON.stringify(
                  (selectedNode || hoveredNode)!.metadata,
                  null,
                  2
                ).slice(0, 200)}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }
}
