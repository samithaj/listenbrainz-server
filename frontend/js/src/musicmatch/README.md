# MusicMatch Graph Visualization

## Overview

This directory contains the frontend components for MusicMatch graph visualization. The implementation provides interactive music graph visualization with multiple layout algorithms.

## Components

### Core Components

1. **MusicGraph.tsx** - Main graph visualization component
   - Canvas-based rendering for performance
   - Interactive node dragging
   - Multiple layout support (force, circular, hierarchical, grid)
   - Node hover and click events
   - Customizable appearance

2. **GraphControls.tsx** - Control panel for graph settings
   - Layout algorithm selection
   - Display options toggle
   - Export and reset functionality

### Utilities

1. **graphLayout.ts** - Layout algorithms and utilities
   - `ForceDirectedLayout` - Physics-based layout with attraction/repulsion
   - `circularLayout` - Arrange nodes in a circle
   - `hierarchicalLayout` - Tree-like level-based arrangement
   - `gridLayout` - Regular grid arrangement
   - Color utilities for nodes and edges by type

## Usage Example

```tsx
import MusicGraph from "./musicmatch/components/MusicGraph";
import GraphControls from "./musicmatch/components/GraphControls";
import { GraphData, LayoutType } from "./musicmatch/utils/graphLayout";

function MyGraphPage() {
  const [graphData, setGraphData] = React.useState<GraphData>({
    nodes: [
      { id: "artist_1", type: "artist", label: "Queen", weight: 100 },
      { id: "track_1", type: "track", label: "Bohemian Rhapsody", weight: 50 }
    ],
    edges: [
      { source: "artist_1", target: "track_1", type: "performed", weight: 1 }
    ]
  });

  const [layoutType, setLayoutType] = React.useState<LayoutType>("force");
  const [showLabels, setShowLabels] = React.useState(true);

  return (
    <div>
      <GraphControls
        layoutType={layoutType}
        showLabels={showLabels}
        onLayoutChange={setLayoutType}
        onShowLabelsChange={setShowLabels}
      />
      <MusicGraph
        graphData={graphData}
        layoutType={layoutType}
        showLabels={showLabels}
        width={800}
        height={600}
        onNodeClick={(node) => console.log("Clicked:", node)}
      />
    </div>
  );
}
```

## API Integration

The components are designed to work with the MusicMatch Graph API:

### Endpoints

- `GET /1/musicmatch/graph/user/<user_name>` - User music graph
- `GET /1/musicmatch/graph/artist/<artist_mbid>` - Artist relationship graph
- `GET /1/musicmatch/graph/genre` - Genre hierarchy/landscape graph

### Example API Call

```typescript
async function fetchUserGraph(username: string, timeRange: string = "month") {
  const response = await fetch(
    `/1/musicmatch/graph/user/${username}?time_range=${timeRange}&graph_type=combined`
  );
  const data = await response.json();
  return data;
}
```

## Current Implementation

### What's Included

✅ Canvas-based rendering for performance with large graphs
✅ Four layout algorithms (force-directed, circular, hierarchical, grid)
✅ Interactive features (drag, hover, click)
✅ Node and edge coloring by type
✅ Responsive design
✅ TypeScript type safety
✅ Customizable display options

### Current Limitations

- Basic force-directed simulation (not using D3's sophisticated algorithms)
- No zoom/pan functionality
- Limited graph filtering options
- No animation transitions between layouts
- Export functionality not yet implemented

## Recommended Enhancements

### For Better Performance and Features

Consider adding these npm packages:

1. **react-force-graph** (or react-force-graph-2d)
   ```bash
   npm install react-force-graph
   ```
   - Built on top of force-graph
   - Better performance for large graphs
   - Built-in zoom/pan
   - WebGL rendering option
   - More sophisticated force simulation

2. **d3-force** (for better physics simulation)
   ```bash
   npm install d3-force
   ```
   - Industry-standard force simulation
   - More forces available (center, collision, links, many-body)
   - Better performance
   - Highly customizable

3. **d3-zoom** (for zoom/pan)
   ```bash
   npm install d3-zoom
   ```
   - Smooth zoom and pan
   - Touch gesture support
   - Programmatic zoom control

4. **vis-network** (alternative approach)
   ```bash
   npm install vis-network
   ```
   - Different rendering approach
   - Rich interaction options
   - Good documentation

### Implementation with D3 Force

If you want to upgrade to D3 force simulation, here's a sketch:

```typescript
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
} from "d3-force";

// In your component
const simulation = forceSimulation(nodes)
  .force("link", forceLink(edges).id((d: any) => d.id).distance(100))
  .force("charge", forceManyBody().strength(-200))
  .force("center", forceCenter(width / 2, height / 2))
  .force("collision", forceCollide().radius(20))
  .on("tick", () => {
    // Update positions and redraw
  });
```

## Performance Considerations

### Current Implementation

- Renders to Canvas (fast for 100s of nodes)
- Request animation frame for smooth updates
- Event delegation for interactions

### For Large Graphs (1000+ nodes)

If you need to handle very large graphs:

1. Use WebGL rendering (via react-force-graph with `ForceGraph3D`)
2. Implement level-of-detail (hide labels when zoomed out)
3. Add clustering for dense graphs
4. Implement virtual scrolling/viewport culling
5. Use Web Workers for layout calculation

## Styling

The components use inline styles and Bootstrap classes. You can customize colors in `graphLayout.ts`:

```typescript
export function getNodeColor(nodeType: string): string {
  const colors = {
    artist: '#1DB954',  // Customize this
    track: '#FF6B6B',   // Customize this
    genre: '#4ECDC4',   // Customize this
  };
  return colors[nodeType as keyof typeof colors] || '#888';
}
```

## Testing

To test the graph visualization:

1. Generate sample graph data
2. Test with varying graph sizes (10, 100, 1000 nodes)
3. Test all layout types
4. Test interactions (drag, hover, click)
5. Test on different screen sizes
6. Test performance with large graphs

## Future Features

- [ ] Zoom and pan controls
- [ ] Graph filtering (by node type, weight threshold)
- [ ] Search/highlight functionality
- [ ] Export as PNG/SVG/JSON
- [ ] Graph analysis metrics (centrality, clusters)
- [ ] Animation between layouts
- [ ] 3D graph visualization
- [ ] Mini-map navigation for large graphs
- [ ] Time-based graph animation
- [ ] Community detection visualization
- [ ] Path highlighting between nodes

## Contributing

When adding new features:

1. Maintain TypeScript types
2. Add JSDoc comments
3. Keep components focused (single responsibility)
4. Update this README
5. Test with various graph sizes
6. Consider performance impact

## License

Same as ListenBrainz-Server project.
