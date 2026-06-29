// src/components/WorkflowBuilder.tsx
"use client";

import React, { useCallback, useState, useEffect } from "react";
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
import { useAuth } from "./Providers";
import { toast } from "sonner";
import { Save, Plus, Edit3, Trash2, HelpCircle } from "lucide-react";

// Node palette definition
const nodeTypes = [
  { type: "start", label: "Start Node" },
  { type: "prompt", label: "AI Prompt Node" },
  { type: "action", label: "Action Webhook Node" },
  { type: "end", label: "End Node" },
];

interface Agent {
  id: number;
  name: string;
  graph: {
    nodes?: Node[];
    edges?: Edge[];
  };
}

export default function WorkflowBuilder() {
  const { token } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // Edit states for selected node
  const [nodeLabel, setNodeLabel] = useState("");
  const [nodePrompt, setNodePrompt] = useState("");
  const [nodeActionUrl, setNodeActionUrl] = useState("");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // Fetch agents on mount
  useEffect(() => {
    if (!token) return;
    fetchAgents();
  }, [token]);

  const fetchAgents = async () => {
    try {
      const res = await fetch(`${API_URL}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
        if (data.length > 0 && selectedAgentId === null) {
          setSelectedAgentId(data[0].id);
        }
      }
    } catch (e) {
      console.error("Error loading agents:", e);
      toast.error("Failed to load agents list");
    }
  };

  // Load selected agent's graph
  useEffect(() => {
    if (selectedAgentId === null) return;
    const agent = agents.find((a) => a.id === selectedAgentId);
    if (agent && agent.graph) {
      setNodes(agent.graph.nodes || []);
      setEdges(agent.graph.edges || []);
      setSelectedNode(null);
    } else {
      setNodes([]);
      setEdges([]);
      setSelectedNode(null);
    }
  }, [selectedAgentId, agents]);

  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds));
  }, [setEdges]);

  const onNodeDragStop = useCallback((event: any, node: Node) => {
    setNodes((nds) => nds.map((n) => (n.id === node.id ? node : n)));
  }, [setNodes]);

  const onNodeClick = useCallback((event: any, node: Node) => {
    setSelectedNode(node);
    setNodeLabel(node.data?.label || "");
    setNodePrompt(node.data?.prompt || "");
    setNodeActionUrl(node.data?.actionUrl || "");
  }, []);

  const addNode = (type: string) => {
    const id = `${type}-${+new Date()}`;
    const newNode: Node = {
      id,
      type: "default",
      data: {
        label: `${type.charAt(0).toUpperCase() + type.slice(1)} Node`,
        nodeType: type,
        prompt: "",
        actionUrl: ""
      },
      position: { x: 200 + Math.random() * 100, y: 100 + Math.random() * 100 },
      style: {
        background: type === "start" ? "rgba(16, 185, 129, 0.25)" : type === "end" ? "rgba(239, 68, 68, 0.25)" : "rgba(30, 41, 59, 0.75)",
        color: "#fff",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        borderRadius: "12px",
        backdropFilter: "blur(8px)",
        padding: "10px",
        fontSize: "12px",
        fontWeight: "bold",
        width: 150,
      }
    };
    setNodes((nds) => nds.concat(newNode));
  };

  const deleteSelectedNode = () => {
    if (!selectedNode) return;
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
    setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
    setSelectedNode(null);
    toast.success("Node removed from canvas");
  };

  const updateNodeProperties = () => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === selectedNode.id) {
          const type = n.data?.nodeType;
          return {
            ...n,
            data: {
              ...n.data,
              label: nodeLabel,
              prompt: nodePrompt,
              actionUrl: nodeActionUrl
            },
            style: {
              ...n.style,
              background: type === "start" ? "rgba(16, 185, 129, 0.25)" : type === "end" ? "rgba(239, 68, 68, 0.25)" : "rgba(30, 41, 59, 0.75)"
            }
          };
        }
        return n;
      })
    );
    toast.success("Node properties updated locally");
  };

  const saveWorkflow = async () => {
    if (!selectedAgentId) {
      toast.error("Please select or create an agent first");
      return;
    }

    try {
      const graph = { nodes, edges };
      const res = await fetch(`${API_URL}/agents/${selectedAgentId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ graph })
      });
      if (res.ok) {
        toast.success("Workflow successfully persisted to database!");
        fetchAgents();
      } else {
        toast.error("Failed to save workflow");
      }
    } catch (e) {
      console.error(e);
      toast.error("Network error saving workflow");
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white font-sans overflow-hidden">
      {/* Sidebar: Control Panel */}
      <div className="w-80 border-r border-zinc-800 bg-zinc-900/60 backdrop-blur-xl flex flex-col p-5 space-y-6">
        <div className="space-y-2">
          <h2 className="text-xl font-black tracking-tight flex items-center gap-2 text-teal-400">
            Auris Canvas
          </h2>
          <p className="text-xs text-slate-400">
            Design interactive call flows and AI system transitions.
          </p>
        </div>

        {/* Agent Selector */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Select Agent</label>
          <select
            className="w-full bg-zinc-950/80 border border-zinc-800 text-sm rounded-xl px-3 py-2.5 outline-none focus:border-teal-500 transition-colors"
            value={selectedAgentId || ""}
            onChange={(e) => setSelectedAgentId(parseInt(e.target.value))}
          >
            {agents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>

        <hr className="border-zinc-800" />

        {/* Node Palette */}
        <div className="space-y-3">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Add Flow Elements</label>
          <div className="grid grid-cols-2 gap-2">
            {nodeTypes.map((n) => (
              <button
                key={n.type}
                onClick={() => addNode(n.type)}
                className="flex items-center justify-center gap-1 text-[11px] font-bold px-2 py-3 rounded-xl bg-zinc-800/80 border border-zinc-700/50 hover:bg-zinc-800 hover:border-teal-500/50 transition-all text-center cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5 text-teal-400" /> {n.label.split(" ")[0]}
              </button>
            ))}
          </div>
        </div>

        <hr className="border-zinc-800" />

        {/* Selected Node Properties */}
        {selectedNode ? (
          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Node Settings</label>
              <button
                onClick={deleteSelectedNode}
                className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 cursor-pointer"
              >
                <Trash2 className="w-3 h-3" /> Delete
              </button>
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <span className="text-[10px] text-slate-500 font-bold uppercase">Node ID</span>
                <p className="text-[11px] font-mono bg-zinc-950 p-1.5 rounded border border-zinc-800 truncate">{selectedNode.id}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] text-slate-500 font-bold uppercase">Label / Title</span>
                <input
                  type="text"
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:border-teal-500 transition-colors"
                  value={nodeLabel}
                  onChange={(e) => setNodeLabel(e.target.value)}
                />
              </div>

              {selectedNode.data?.nodeType === "prompt" && (
                <div className="space-y-1">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">AI Prompt / Instruction</span>
                  <textarea
                    rows={4}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:border-teal-500 transition-colors resize-none"
                    value={nodePrompt}
                    onChange={(e) => setNodePrompt(e.target.value)}
                    placeholder="Enter instructions for the AI agent on what to say..."
                  />
                </div>
              )}

              {selectedNode.data?.nodeType === "action" && (
                <div className="space-y-1">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">Webhook Endpoint URL</span>
                  <input
                    type="text"
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:border-teal-500 transition-colors"
                    value={nodeActionUrl}
                    onChange={(e) => setNodeActionUrl(e.target.value)}
                    placeholder="https://api.yourdomain.com/webhook"
                  />
                </div>
              )}

              <button
                onClick={updateNodeProperties}
                className="w-full py-2 bg-zinc-800 hover:bg-zinc-700/80 border border-zinc-700/50 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
              >
                <Edit3 className="w-3.5 h-3.5" /> Apply Settings
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-4 border border-dashed border-zinc-800 rounded-2xl bg-zinc-950/20 text-slate-500">
            <HelpCircle className="w-8 h-8 text-zinc-700 mb-2" />
            <p className="text-xs">Click a node on the canvas to configure prompts, variables, and transitions.</p>
          </div>
        )}

        {/* Persistence Controls */}
        <button
          onClick={saveWorkflow}
          className="w-full py-3 bg-teal-500 hover:bg-teal-400 text-slate-950 font-black rounded-xl text-sm flex items-center justify-center gap-2 cursor-pointer transition-colors"
        >
          <Save className="w-4 h-4" /> Save Workflow
        </button>
      </div>

      {/* Canvas */}
      <div className="flex-1 bg-[#0b0c10] relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDragStop={onNodeDragStop}
          onNodeClick={onNodeClick}
          fitView
        >
          <Background color="rgba(255,255,255,0.05)" variant="dots" gap={16} size={1} />
          <MiniMap
            nodeColor={(node) => {
              if (node.data?.nodeType === "start") return "rgba(16, 185, 129, 0.4)";
              if (node.data?.nodeType === "end") return "rgba(239, 68, 68, 0.4)";
              return "rgba(255,255,255,0.2)";
            }}
            nodeStrokeWidth={3}
            maskColor="rgba(0,0,0,0.6)"
            style={{ background: "#18181b", border: "1px solid #27272a" }}
          />
          <Controls showInteractive={true} style={{ display: "flex", flexDirection: "row", gap: "2px" }} />
        </ReactFlow>
      </div>
    </div>
  );
}
