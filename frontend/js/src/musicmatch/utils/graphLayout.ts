/**
 * Graph Layout Utilities
 *
 * Provides layout algorithms and utilities for music graph visualization
 */

export interface GraphNode {
  id: string;
  type: 'artist' | 'track' | 'genre';
  label: string;
  mbid?: string;
  weight?: number;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  metadata?: any;
}

export interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata?: any;
}

export interface LayoutConfig {
  width: number;
  height: number;
  centerX?: number;
  centerY?: number;
  nodeRadius?: number;
  linkDistance?: number;
  chargeStrength?: number;
}

/**
 * Force-directed layout using simulation
 * This is a simple implementation that can be enhanced with D3 force simulation
 */
export class ForceDirectedLayout {
  private nodes: GraphNode[];
  private edges: GraphEdge[];
  private config: LayoutConfig;
  private isRunning: boolean = false;
  private animationFrame: number | null = null;

  constructor(graphData: GraphData, config: LayoutConfig) {
    this.nodes = [...graphData.nodes];
    this.edges = [...graphData.edges];
    this.config = {
      centerX: config.width / 2,
      centerY: config.height / 2,
      nodeRadius: 5,
      linkDistance: 50,
      chargeStrength: -30,
      ...config,
    };

    this.initializePositions();
  }

  /**
   * Initialize random positions for nodes
   */
  private initializePositions(): void {
    this.nodes.forEach((node) => {
      if (node.x === undefined) {
        node.x = this.config.centerX! + (Math.random() - 0.5) * 100;
      }
      if (node.y === undefined) {
        node.y = this.config.centerY! + (Math.random() - 0.5) * 100;
      }
      node.vx = 0;
      node.vy = 0;
    });
  }

  /**
   * Run simulation step
   */
  tick(alpha: number = 1): GraphData {
    const { linkDistance = 50, chargeStrength = -30 } = this.config;

    // Apply forces
    this.nodes.forEach((node) => {
      if (node.fx !== null && node.fx !== undefined) {
        node.x = node.fx;
        node.vx = 0;
      }
      if (node.fy !== null && node.fy !== undefined) {
        node.y = node.fy;
        node.vy = 0;
      }
    });

    // Link force
    this.edges.forEach((edge) => {
      const source = this.getNode(edge.source);
      const target = this.getNode(edge.target);
      if (!source || !target) return;

      const dx = target.x! - source.x!;
      const dy = target.y! - source.y!;
      const distance = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (distance - linkDistance) * alpha * 0.1;

      const fx = (dx / distance) * force;
      const fy = (dy / distance) * force;

      source.vx! += fx;
      source.vy! += fy;
      target.vx! -= fx;
      target.vy! -= fy;
    });

    // Charge force (repulsion between nodes)
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const a = this.nodes[i];
        const b = this.nodes[j];

        const dx = b.x! - a.x!;
        const dy = b.y! - a.y!;
        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (chargeStrength * alpha) / (distance * distance);

        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;

        a.vx! -= fx;
        a.vy! -= fy;
        b.vx! += fx;
        b.vy! += fy;
      }
    }

    // Update positions
    this.nodes.forEach((node) => {
      if (node.fx === null || node.fx === undefined) {
        node.x! += node.vx! * alpha;
      }
      if (node.fy === null || node.fy === undefined) {
        node.y! += node.vy! * alpha;
      }

      // Apply damping
      node.vx! *= 0.9;
      node.vy! *= 0.9;
    });

    return {
      nodes: this.nodes,
      edges: this.edges,
    };
  }

  private getNode(nodeOrId: string | GraphNode): GraphNode | undefined {
    if (typeof nodeOrId === 'string') {
      return this.nodes.find((n) => n.id === nodeOrId);
    }
    return nodeOrId;
  }

  /**
   * Start continuous simulation
   */
  start(onTick: (data: GraphData) => void, iterations: number = 300): void {
    this.isRunning = true;
    let iteration = 0;

    const animate = () => {
      if (!this.isRunning || iteration >= iterations) {
        this.isRunning = false;
        return;
      }

      const alpha = Math.max(0, 1 - iteration / iterations);
      const data = this.tick(alpha);
      onTick(data);

      iteration++;
      this.animationFrame = requestAnimationFrame(animate);
    };

    animate();
  }

  /**
   * Stop simulation
   */
  stop(): void {
    this.isRunning = false;
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
  }

  /**
   * Fix node position
   */
  fixNode(nodeId: string, x: number, y: number): void {
    const node = this.nodes.find((n) => n.id === nodeId);
    if (node) {
      node.fx = x;
      node.fy = y;
    }
  }

  /**
   * Release fixed node
   */
  releaseNode(nodeId: string): void {
    const node = this.nodes.find((n) => n.id === nodeId);
    if (node) {
      node.fx = null;
      node.fy = null;
    }
  }
}

/**
 * Circular layout - arranges nodes in a circle
 */
export function circularLayout(
  graphData: GraphData,
  config: LayoutConfig
): GraphData {
  const { width, height, centerX = width / 2, centerY = height / 2 } = config;
  const radius = Math.min(width, height) * 0.4;
  const angleStep = (2 * Math.PI) / graphData.nodes.length;

  const nodes = graphData.nodes.map((node, index) => ({
    ...node,
    x: centerX + radius * Math.cos(index * angleStep),
    y: centerY + radius * Math.sin(index * angleStep),
  }));

  return {
    ...graphData,
    nodes,
  };
}

/**
 * Hierarchical layout - arranges nodes in levels
 */
export function hierarchicalLayout(
  graphData: GraphData,
  config: LayoutConfig,
  rootNodeId?: string
): GraphData {
  const { width, height } = config;
  const levels = new Map<string, number>();
  const nodesByLevel = new Map<number, GraphNode[]>();

  // Determine levels using BFS
  const queue: Array<{ nodeId: string; level: number }> = [];

  // Start from root node or first node
  const startNode = rootNodeId
    ? graphData.nodes.find((n) => n.id === rootNodeId)
    : graphData.nodes[0];

  if (startNode) {
    queue.push({ nodeId: startNode.id, level: 0 });
    levels.set(startNode.id, 0);
  }

  while (queue.length > 0) {
    const { nodeId, level } = queue.shift()!;

    // Find connected nodes
    graphData.edges.forEach((edge) => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;

      let nextNodeId: string | null = null;
      if (sourceId === nodeId && !levels.has(targetId)) {
        nextNodeId = targetId;
      } else if (targetId === nodeId && !levels.has(sourceId)) {
        nextNodeId = sourceId;
      }

      if (nextNodeId) {
        levels.set(nextNodeId, level + 1);
        queue.push({ nodeId: nextNodeId, level: level + 1 });
      }
    });
  }

  // Assign remaining unconnected nodes to level 0
  graphData.nodes.forEach((node) => {
    if (!levels.has(node.id)) {
      levels.set(node.id, 0);
    }
  });

  // Group nodes by level
  graphData.nodes.forEach((node) => {
    const level = levels.get(node.id) || 0;
    if (!nodesByLevel.has(level)) {
      nodesByLevel.set(level, []);
    }
    nodesByLevel.get(level)!.push(node);
  });

  const maxLevel = Math.max(...Array.from(levels.values()));
  const levelHeight = height / (maxLevel + 1);

  // Position nodes
  const nodes = graphData.nodes.map((node) => {
    const level = levels.get(node.id) || 0;
    const nodesInLevel = nodesByLevel.get(level) || [];
    const indexInLevel = nodesInLevel.indexOf(node);
    const levelWidth = width / (nodesInLevel.length + 1);

    return {
      ...node,
      x: levelWidth * (indexInLevel + 1),
      y: levelHeight * (level + 0.5),
    };
  });

  return {
    ...graphData,
    nodes,
  };
}

/**
 * Grid layout - arranges nodes in a grid
 */
export function gridLayout(graphData: GraphData, config: LayoutConfig): GraphData {
  const { width, height } = config;
  const cols = Math.ceil(Math.sqrt(graphData.nodes.length));
  const rows = Math.ceil(graphData.nodes.length / cols);
  const cellWidth = width / cols;
  const cellHeight = height / rows;

  const nodes = graphData.nodes.map((node, index) => ({
    ...node,
    x: (index % cols) * cellWidth + cellWidth / 2,
    y: Math.floor(index / cols) * cellHeight + cellHeight / 2,
  }));

  return {
    ...graphData,
    nodes,
  };
}

/**
 * Get node color by type
 */
export function getNodeColor(nodeType: string): string {
  const colors = {
    artist: '#1DB954', // Spotify green
    track: '#FF6B6B', // Coral red
    genre: '#4ECDC4', // Turquoise
  };
  return colors[nodeType as keyof typeof colors] || '#888';
}

/**
 * Get edge color by type
 */
export function getEdgeColor(edgeType: string): string {
  const colors = {
    performed: '#888',
    collaboration: '#4ECDC4',
    similar: '#95E1D3',
    member_of: '#F38181',
    parent_of: '#AA96DA',
    related: '#FCBAD3',
  };
  return colors[edgeType as keyof typeof colors] || '#ccc';
}
