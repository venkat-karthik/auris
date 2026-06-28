// src/components/WorkflowBuilder.tsx
import React, { useCallback, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  Connection,
  Edge,
  Node,
  useEdgesState,
  useNodesState,
} from "react-flow-renderer";

// Node palette definition
const nodeTypes = [
  { type: "start", label: "Start" },
  { type: "prompt", label: "Prompt" },
  { type: "action", label: "Action" },
  { type: "end", label: "End" },
];

export default function WorkflowBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds));
  }, []);

  const onNodeDragStop = useCallback((event, node) => {
    // optional: update node position in state
    setNodes((nds) => nds.map((n) => (n.id === node.id ? node : n)));
  }, []);

  const addNode = (type: string) => {
    const newNode: Node = {
      id: `${type}-${+new Date()}`,
      type: "default",
      data: { label: `${type.charAt(0).toUpperCase() + type.slice(1)}` },
      position: { x: 250, y: 150 },
    };
    setNodes((nds) => nds.concat(newNode));
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 via-slate-800 to-gray-700 p-4">
      {/* Toolbar */}
      <div className="w-56 mr-4 bg-white/10 backdrop-blur-md rounded-lg p-3 space-y-2">
        <h2 className="text-sm font-medium text-white/80 mb-2">Palette</h2>
        {nodeTypes.map((n) => (
          <button
            key={n.type}
            className="w-full text-left px-2 py-1 rounded hover:bg-white/20 transition-colors text-white"
            onClick={() => addNode(n.type)}
          >
            {n.label}
          </button>
        ))}
      </div>

      {/* Canvas */}
      <div className="flex-1 bg-white/5 backdrop-blur-md rounded-lg overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDragStop={onNodeDragStop}
          fitView
        >
          <Background color="#222" variant="dots" gap={12} />
          <MiniMap nodeColor={() => "#fff"} nodeStrokeWidth={3} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  );
}
