"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";

interface GraphNode {
  id: string;
  name: string;
  type: "function" | "class" | "method" | string;
  filepath: string;
  line: number;
}

interface GraphEdge {
  source: string;
  target: string;
  type: "calls" | "inherits" | string;
}

interface GraphViewerProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  nodeCount: number;
  edgeCount: number;
}

const TYPE_COLORS: Record<string, string> = {
  class: "#a78bfa",    // purple
  function: "#34d399", // emerald
  method: "#60a5fa",   // blue
  default: "#9ca3af",  // gray
};

export default function GraphViewer({ nodes, edges, nodeCount, edgeCount }: GraphViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [search, setSearch] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filterType, setFilterType] = useState("all");
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});
  const animationRef = useRef<number>(0);

  const filteredNodes = nodes.filter(n => {
    const matchSearch = !search || n.name.toLowerCase().includes(search.toLowerCase()) || n.filepath.toLowerCase().includes(search.toLowerCase());
    const matchType = filterType === "all" || n.type === filterType;
    return matchSearch && matchType;
  });

  const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
  const filteredEdges = edges.filter(e => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target));

  // Initialize positions with force-directed layout approximation
  useEffect(() => {
    if (filteredNodes.length === 0) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const W = canvas.width;
    const H = canvas.height;

    const pos: Record<string, { x: number; y: number }> = {};
    // Arrange in a circle
    filteredNodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / filteredNodes.length;
      const r = Math.min(W, H) * 0.35;
      pos[node.id] = {
        x: W / 2 + r * Math.cos(angle),
        y: H / 2 + r * Math.sin(angle),
      };
    });
    setPositions(pos);
  }, [filteredNodes.length, filterType, search]);

  // Draw the graph
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || filteredNodes.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background
    ctx.fillStyle = "#09090b";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (Object.keys(positions).length === 0) return;

    // Draw edges
    filteredEdges.forEach(edge => {
      const src = positions[edge.source];
      const dst = positions[edge.target];
      if (!src || !dst) return;
      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(dst.x, dst.y);
      ctx.strokeStyle = edge.type === "inherits" ? "rgba(167,139,250,0.4)" : "rgba(52,211,153,0.25)";
      ctx.lineWidth = 1;
      ctx.stroke();

      // Arrowhead
      const angle = Math.atan2(dst.y - src.y, dst.x - src.x);
      const arrowLen = 8;
      ctx.beginPath();
      ctx.moveTo(dst.x, dst.y);
      ctx.lineTo(dst.x - arrowLen * Math.cos(angle - 0.4), dst.y - arrowLen * Math.sin(angle - 0.4));
      ctx.lineTo(dst.x - arrowLen * Math.cos(angle + 0.4), dst.y - arrowLen * Math.sin(angle + 0.4));
      ctx.closePath();
      ctx.fillStyle = edge.type === "inherits" ? "rgba(167,139,250,0.6)" : "rgba(52,211,153,0.5)";
      ctx.fill();
    });

    // Draw nodes
    filteredNodes.forEach(node => {
      const pos = positions[node.id];
      if (!pos) return;
      const color = TYPE_COLORS[node.type] || TYPE_COLORS.default;
      const isSelected = selectedNode?.id === node.id;
      const radius = isSelected ? 10 : 7;

      // Glow
      if (isSelected) {
        const grd = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, 24);
        grd.addColorStop(0, color + "60");
        grd.addColorStop(1, "transparent");
        ctx.fillStyle = grd;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 24, 0, Math.PI * 2);
        ctx.fill();
      }

      // Node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      // Label for selected or few nodes
      if (isSelected || filteredNodes.length <= 40) {
        ctx.fillStyle = "#e4e4e7";
        ctx.font = `${isSelected ? "bold " : ""}10px monospace`;
        ctx.textAlign = "center";
        ctx.fillText(node.name.slice(0, 20), pos.x, pos.y - 14);
      }
    });
  }, [positions, filteredNodes, filteredEdges, selectedNode]);

  // Canvas click to select node
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    let found: GraphNode | null = null;
    for (const node of filteredNodes) {
      const pos = positions[node.id];
      if (!pos) continue;
      const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (dist <= 14) {
        found = node;
        break;
      }
    }
    setSelectedNode(found);
  };

  // Get connections of selected node
  const selectedConnections = selectedNode
    ? filteredEdges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
    : [];

  return (
    <div className="space-y-4">
      {/* Stats bar */}
      <div className="flex flex-wrap gap-4 text-xs text-zinc-400">
        <span className="px-3 py-1 bg-zinc-900 border border-zinc-800 rounded-full">
          <span className="font-bold text-purple-400">{nodeCount}</span> nodes
        </span>
        <span className="px-3 py-1 bg-zinc-900 border border-zinc-800 rounded-full">
          <span className="font-bold text-emerald-400">{edgeCount}</span> edges
        </span>
        <span className="px-3 py-1 bg-zinc-900 border border-zinc-800 rounded-full flex gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-purple-400 mt-0.5"></span>class
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 mt-0.5 ml-2"></span>function
          <span className="inline-block w-2 h-2 rounded-full bg-blue-400 mt-0.5 ml-2"></span>method
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by name or file..."
          className="flex-1 min-w-48 px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder:text-zinc-500 text-sm focus:outline-none focus:border-purple-500"
        />
        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          className="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-300 text-sm focus:outline-none focus:border-purple-500"
        >
          <option value="all">All Types</option>
          <option value="class">Classes</option>
          <option value="function">Functions</option>
          <option value="method">Methods</option>
        </select>
      </div>

      <div className="flex flex-col lg:flex-row gap-4">
        {/* Canvas */}
        <div className="flex-1 border border-zinc-800 rounded-xl overflow-hidden">
          <canvas
            ref={canvasRef}
            width={800}
            height={500}
            onClick={handleCanvasClick}
            className="w-full cursor-crosshair"
            style={{ background: "#09090b" }}
          />
        </div>

        {/* Selected node details panel */}
        {selectedNode && (
          <div className="w-full lg:w-72 p-5 bg-zinc-900 border border-purple-500/30 rounded-xl space-y-4 text-sm shrink-0">
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-2">Selected Node</p>
              <p className="text-white font-bold text-base">{selectedNode.name}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full border mt-1 inline-block ${
                selectedNode.type === "class" ? "text-purple-400 border-purple-500/20 bg-purple-500/10" :
                selectedNode.type === "function" ? "text-emerald-400 border-emerald-500/20 bg-emerald-500/10" :
                "text-blue-400 border-blue-500/20 bg-blue-500/10"
              }`}>
                {selectedNode.type}
              </span>
            </div>
            <div>
              <p className="text-xs text-zinc-500 mb-1">Location</p>
              <p className="font-mono text-xs text-teal-400 break-all">{selectedNode.filepath}:{selectedNode.line}</p>
            </div>
            {selectedConnections.length > 0 && (
              <div>
                <p className="text-xs text-zinc-500 mb-2">Connections ({selectedConnections.length})</p>
                <div className="space-y-1 max-h-52 overflow-y-auto">
                  {selectedConnections.slice(0, 15).map((edge, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        edge.type === "inherits" ? "bg-purple-500/20 text-purple-400" : "bg-emerald-500/20 text-emerald-400"
                      }`}>
                        {edge.type}
                      </span>
                      <span className="text-zinc-300 font-mono truncate">
                        {edge.source === selectedNode.id ? `→ ${edge.target.split("::").pop()}` : `← ${edge.source.split("::").pop()}`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <button
              onClick={() => setSelectedNode(null)}
              className="w-full text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              Deselect
            </button>
          </div>
        )}
      </div>

      <p className="text-xs text-zinc-600">Click a node to see details and connections. Showing {filteredNodes.length} of {nodeCount} nodes.</p>
    </div>
  );
}
