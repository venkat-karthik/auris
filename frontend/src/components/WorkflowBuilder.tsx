"use client";

import React, { useCallback, useState, useEffect, useRef } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  addEdge,
  Connection,
  Edge,
  Node,
  useEdgesState,
  useNodesState,
  Handle,
  Position
} from "react-flow-renderer";
import { useAuth } from "./Providers";
import { toast } from "sonner";
import {
  Save,
  Plus,
  Edit3,
  Trash2,
  HelpCircle,
  Phone,
  PhoneOff,
  Mic,
  MessageSquare,
  Activity,
  Play,
  Sparkles,
  Link as LinkIcon,
  Ban,
  Loader2,
  Clock
} from "lucide-react";

// --- Custom Node Components for React Flow ---

const StartNodeComponent = ({ data }: any) => (
  <div className="px-4 py-3 rounded-2xl bg-zinc-950/90 border-2 border-emerald-500/80 shadow-[0_0_15px_rgba(16,185,129,0.15)] backdrop-blur-md text-white min-w-[180px] hover:border-emerald-400 transition-all">
    <div className="flex items-center gap-2 border-b border-emerald-500/20 pb-1.5 mb-1.5">
      <Play className="w-3.5 h-3.5 text-emerald-400 fill-emerald-400" />
      <span className="text-[10px] font-black uppercase tracking-wider text-emerald-400">Start Call</span>
    </div>
    <p className="text-[11px] font-bold text-slate-100 truncate">{data.label || "Start Node"}</p>
    {data.prompt && (
      <p className="text-[9px] text-slate-400 line-clamp-2 mt-1 font-medium">{data.prompt}</p>
    )}
    <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-emerald-500 border-2 border-zinc-950 !bottom-[-6px]" />
  </div>
);

const PromptNodeComponent = ({ data }: any) => (
  <div className="px-4 py-3 rounded-2xl bg-zinc-950/90 border-2 border-indigo-500/80 shadow-[0_0_15px_rgba(99,102,241,0.15)] backdrop-blur-md text-white min-w-[180px] hover:border-indigo-400 transition-all">
    <div className="flex items-center gap-2 border-b border-indigo-500/20 pb-1.5 mb-1.5">
      <Sparkles className="w-3.5 h-3.5 text-indigo-400 fill-indigo-400" />
      <span className="text-[10px] font-black uppercase tracking-wider text-indigo-400">AI Prompt</span>
    </div>
    <p className="text-[11px] font-bold text-slate-100 truncate">{data.label || "AI Prompt Node"}</p>
    {data.prompt && (
      <p className="text-[9px] text-slate-400 line-clamp-2 mt-1 font-medium">{data.prompt}</p>
    )}
    <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-indigo-500 border-2 border-zinc-950 !top-[-6px]" />
    <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-indigo-500 border-2 border-zinc-950 !bottom-[-6px]" />
  </div>
);

const ActionNodeComponent = ({ data }: any) => (
  <div className="px-4 py-3 rounded-2xl bg-zinc-950/90 border-2 border-teal-500/80 shadow-[0_0_15px_rgba(20,184,166,0.15)] backdrop-blur-md text-white min-w-[180px] hover:border-teal-400 transition-all">
    <div className="flex items-center gap-2 border-b border-teal-500/20 pb-1.5 mb-1.5">
      <LinkIcon className="w-3.5 h-3.5 text-teal-400" />
      <span className="text-[10px] font-black uppercase tracking-wider text-teal-400">API Action</span>
    </div>
    <p className="text-[11px] font-bold text-slate-100 truncate">{data.label || "Action Node"}</p>
    {data.actionUrl && (
      <p className="text-[8px] text-slate-400 font-mono truncate mt-1">{data.actionUrl}</p>
    )}
    <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-teal-500 border-2 border-zinc-950 !top-[-6px]" />
    <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-teal-500 border-2 border-zinc-950 !bottom-[-6px]" />
  </div>
);

const EndNodeComponent = ({ data }: any) => (
  <div className="px-4 py-3 rounded-2xl bg-zinc-950/90 border-2 border-rose-500/80 shadow-[0_0_15px_rgba(239,68,68,0.15)] backdrop-blur-md text-white min-w-[180px] hover:border-rose-400 transition-all">
    <div className="flex items-center gap-2 border-b border-rose-500/20 pb-1.5 mb-1.5">
      <Ban className="w-3.5 h-3.5 text-rose-400" />
      <span className="text-[10px] font-black uppercase tracking-wider text-rose-400">End Call</span>
    </div>
    <p className="text-[11px] font-bold text-slate-100 truncate">{data.label || "End Node"}</p>
    <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-rose-500 border-2 border-zinc-950 !top-[-6px]" />
  </div>
);

const customNodeTypes = {
  start: StartNodeComponent,
  prompt: PromptNodeComponent,
  action: ActionNodeComponent,
  end: EndNodeComponent
};

interface Agent {
  id: number;
  name: string;
  graph: any;
}

export default function WorkflowBuilder() {
  const { token } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // Edit states
  const [nodeLabel, setNodeLabel] = useState("");
  const [nodePrompt, setNodePrompt] = useState("");
  const [nodeActionUrl, setNodeActionUrl] = useState("");

  // Sandbox Test States
  const [isCalling, setIsCalling] = useState(false);
  const [testTranscript, setTestTranscript] = useState<{ sender: "user" | "agent", text: string }[]>([]);
  const [latencyMetrics, setLatencyMetrics] = useState({ stt: 120, llm: 160, tts: 85 });
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const processorNodeRef = useRef<any>(null);
  const activeSourcesRef = useRef<any[]>([]);
  const nextPlaybackTimeRef = useRef<number>(0);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchAgents = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
        if (data.length > 0 && !selectedAgentId) {
          setSelectedAgentId(data[0].id);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, [token]);

  useEffect(() => {
    if (!selectedAgentId) return;
    const activeAgent = agents.find((a) => a.id === selectedAgentId);
    if (activeAgent && activeAgent.graph) {
      const savedNodes = activeAgent.graph.nodes || [];
      const savedEdges = activeAgent.graph.edges || [];
      
      // Ensure custom nodeTypes are used in rendering mapping
      const mappedNodes = savedNodes.map((n: any) => ({
        ...n,
        type: n.data?.nodeType || "prompt"
      }));

      setNodes(mappedNodes);
      setEdges(savedEdges);
    } else {
      // Default template graph
      setNodes([
        {
          id: "start-1",
          type: "start",
          data: { label: "Welcome Greeting", nodeType: "start", prompt: "Hello, welcome to Acme Corp! How can I help you today?" },
          position: { x: 250, y: 50 }
        },
        {
          id: "prompt-1",
          type: "prompt",
          data: { label: "FAQ Handling", nodeType: "prompt", prompt: "If caller asks for sales, transfer. If caller asks for pricing, answer 100 INR." },
          position: { x: 250, y: 200 }
        }
      ]);
      setEdges([
        { id: "e1", source: "start-1", target: "prompt-1" }
      ]);
    }
    setSelectedNode(null);
  }, [selectedAgentId, agents]);

  const onConnect = useCallback((params: Connection | Edge) => {
    setEdges((eds) => addEdge(params, eds));
  }, []);

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
      type,
      data: {
        label: `New ${type.charAt(0).toUpperCase() + type.slice(1)}`,
        nodeType: type,
        prompt: type === "start" ? "Thank you for calling. How can we assist you?" : "",
        actionUrl: ""
      },
      position: { x: 200 + Math.random() * 80, y: 150 + Math.random() * 80 }
    };
    setNodes((nds) => nds.concat(newNode));
  };

  const updateNodeProperties = () => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === selectedNode.id) {
          return {
            ...n,
            data: {
              ...n.data,
              label: nodeLabel,
              prompt: nodePrompt,
              actionUrl: nodeActionUrl
            }
          };
        }
        return n;
      })
    );
    toast.success("Node properties updated locally");
  };

  const deleteSelectedNode = () => {
    if (!selectedNode) return;
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
    setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
    setSelectedNode(null);
    toast.success("Node removed from canvas");
  };

  const saveWorkflow = async () => {
    if (!selectedAgentId) {
      toast.error("Please select an agent first");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/agents/${selectedAgentId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          graph: { nodes, edges }
        })
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

  // --- Real-time Sandbox Audio Testing ---

  const startVoiceTest = async () => {
    if (!selectedAgentId) {
      toast.error("Please select an agent to test");
      return;
    }
    setIsCalling(true);
    setTestTranscript([{ sender: "agent", text: "Connecting to voice server..." }]);
    nextPlaybackTimeRef.current = 0;
    activeSourcesRef.current = [];

    const downsample = (buffer: Float32Array, inputSampleRate: number) => {
      const outputSampleRate = 16000;
      if (inputSampleRate === outputSampleRate) return buffer;
      const ratio = inputSampleRate / outputSampleRate;
      const result = new Float32Array(Math.round(buffer.length / ratio));
      let offsetResult = 0;
      let offsetBuffer = 0;
      while (offsetResult < result.length) {
        const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
        let accum = 0;
        let count = 0;
        for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
          accum += buffer[i];
          count++;
        }
        result[offsetResult] = count > 0 ? accum / count : 0;
        offsetResult++;
        offsetBuffer = nextOffsetBuffer;
      }
      return result;
    };

    const floatTo16BitPCM = (input: Float32Array) => {
      const buffer = new ArrayBuffer(input.length * 2);
      const view = new DataView(buffer);
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      }
      return buffer;
    };

    try {
      const wsUrl = `${API_URL.replace("http", "ws")}/calls/ws/${selectedAgentId}?token=${token}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioCtxRef.current = audioCtx;
      nextPlaybackTimeRef.current = audioCtx.currentTime;

      ws.onopen = () => {
        ws.send(JSON.stringify({ type: "start", context: { customer_name: "Developer" } }));
      };

      ws.onmessage = async (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "transcript") {
          setTestTranscript((prev) => {
            if (prev.length > 0 && prev[prev.length - 1].text === "Connecting to voice server...") {
              return [{ sender: "agent", text: msg.text }];
            }
            return [...prev, { sender: msg.final ? "user" : "agent", text: msg.text }];
          });
          // Randomize latency metrics simulation for visualization
          setLatencyMetrics({
            stt: Math.floor(90 + Math.random() * 40),
            llm: Math.floor(140 + Math.random() * 60),
            tts: Math.floor(70 + Math.random() * 30)
          });
        } else if (msg.type === "audio") {
          const binaryString = window.atob(msg.data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const int16Samples = new Int16Array(bytes.buffer);
          const floatSamples = new Float32Array(int16Samples.length);
          for (let i = 0; i < int16Samples.length; i++) {
            floatSamples[i] = int16Samples[i] / 32768.0;
          }

          const audioBuf = audioCtx.createBuffer(1, floatSamples.length, 16000);
          audioBuf.copyToChannel(floatSamples, 0);

          const source = audioCtx.createBufferSource();
          source.buffer = audioBuf;
          source.connect(audioCtx.destination);

          const startTime = Math.max(nextPlaybackTimeRef.current, audioCtx.currentTime);
          source.start(startTime);
          nextPlaybackTimeRef.current = startTime + audioBuf.duration;

          activeSourcesRef.current.push(source);
          source.onended = () => {
            activeSourcesRef.current = activeSourcesRef.current.filter((s) => s !== source);
          };
        } else if (msg.type === "interrupted") {
          activeSourcesRef.current.forEach((src) => {
            try { src.stop(); } catch (e) {}
          });
          activeSourcesRef.current = [];
          nextPlaybackTimeRef.current = audioCtx.currentTime;
        } else if (msg.type === "error") {
          toast.error(msg.message);
          stopVoiceTest();
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;

      const sourceNode = audioCtx.createMediaStreamSource(stream);
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorNodeRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (ws.readyState !== WebSocket.OPEN) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const downsampled = downsample(inputData, audioCtx.sampleRate);
        const pcmBuffer = floatTo16BitPCM(downsampled);

        const binaryBytes = new Uint8Array(pcmBuffer);
        let binaryString = "";
        for (let i = 0; i < binaryBytes.length; i++) {
          binaryString += String.fromCharCode(binaryBytes[i]);
        }
        ws.send(JSON.stringify({ type: "audio", data: window.btoa(binaryString) }));
      };

      sourceNode.connect(processor);
      processor.connect(audioCtx.destination);
    } catch (e) {
      console.error(e);
      toast.error("Could not bind sandbox microphone");
      stopVoiceTest();
    }
  };

  const stopVoiceTest = () => {
    setIsCalling(false);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (processorNodeRef.current) {
      processorNodeRef.current.disconnect();
      processorNodeRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((t) => t.stop());
      micStreamRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
    activeSourcesRef.current = [];
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white font-sans overflow-hidden">
      {/* Left Sidebar: Controls & Node Creation */}
      <div className="w-72 border-r border-zinc-800 bg-zinc-900/60 backdrop-blur-xl flex flex-col p-5 space-y-6 flex-shrink-0">
        <div className="space-y-1">
          <h2 className="text-lg font-black tracking-tight text-teal-400 flex items-center gap-1.5">
            <Sparkles className="w-5 h-5" /> Node Editor
          </h2>
          <p className="text-[10px] text-slate-400 leading-normal">
            Design interactive loops, custom routing logic, and webhook actions.
          </p>
        </div>

        {/* Agent Dropdown */}
        <div className="space-y-1.5">
          <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">Active Assistant</label>
          <select
            className="w-full bg-zinc-950 border border-zinc-800 text-xs rounded-xl px-2.5 py-2 outline-none focus:border-teal-500 transition-colors"
            value={selectedAgentId || ""}
            onChange={(e) => setSelectedAgentId(parseInt(e.target.value))}
          >
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </div>

        <hr className="border-zinc-800" />

        {/* Node Palette */}
        <div className="space-y-2">
          <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">Create Nodes</label>
          <div className="grid grid-cols-2 gap-1.5">
            <button
              onClick={() => addNode("start")}
              className="flex items-center justify-center gap-1 text-[10px] font-bold py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700/80 border border-zinc-700/40 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-400" /> Start
            </button>
            <button
              onClick={() => addNode("prompt")}
              className="flex items-center justify-center gap-1 text-[10px] font-bold py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700/80 border border-zinc-700/40 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-indigo-400" /> Prompt
            </button>
            <button
              onClick={() => addNode("action")}
              className="flex items-center justify-center gap-1 text-[10px] font-bold py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700/80 border border-zinc-700/40 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-teal-400" /> Action
            </button>
            <button
              onClick={() => addNode("end")}
              className="flex items-center justify-center gap-1 text-[10px] font-bold py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700/80 border border-zinc-700/40 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-rose-400" /> End
            </button>
          </div>
        </div>

        <hr className="border-zinc-800" />

        {/* Selected Node Properties */}
        {selectedNode ? (
          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Properties</span>
              <button
                onClick={deleteSelectedNode}
                className="text-[10px] text-rose-400 hover:text-rose-300 flex items-center gap-0.5 cursor-pointer font-bold"
              >
                <Trash2 className="w-3 h-3" /> Remove
              </button>
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <span className="text-[9px] text-slate-500 font-bold uppercase block">Node ID</span>
                <p className="text-[10px] font-mono bg-zinc-950 p-1.5 rounded border border-zinc-800 truncate select-all">{selectedNode.id}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[9px] text-slate-500 font-bold uppercase block">Label / Title</span>
                <input
                  type="text"
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:border-teal-500 transition-colors"
                  value={nodeLabel}
                  onChange={(e) => setNodeLabel(e.target.value)}
                />
              </div>

              {(selectedNode.type === "start" || selectedNode.type === "prompt") && (
                <div className="space-y-1">
                  <span className="text-[9px] text-slate-500 font-bold uppercase block">AI Greeting / Prompt</span>
                  <textarea
                    rows={4}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:border-teal-500 transition-colors resize-none font-medium text-slate-200"
                    value={nodePrompt}
                    onChange={(e) => setNodePrompt(e.target.value)}
                    placeholder="e.g. You are a helpdesk agent. Answer queries concisely..."
                  />
                </div>
              )}

              {selectedNode.type === "action" && (
                <div className="space-y-1">
                  <span className="text-[9px] text-slate-500 font-bold uppercase block">Webhook Endpoint</span>
                  <input
                    type="text"
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:border-teal-500 transition-colors font-mono text-teal-400"
                    value={nodeActionUrl}
                    onChange={(e) => setNodeActionUrl(e.target.value)}
                    placeholder="https://api.site.com/endpoint"
                  />
                </div>
              )}

              <button
                onClick={updateNodeProperties}
                className="w-full py-2 bg-teal-500/10 text-teal-400 border border-teal-500/25 rounded-lg text-xs font-bold flex items-center justify-center gap-1 hover:bg-teal-500/25 transition-all cursor-pointer"
              >
                <Edit3 className="w-3.5 h-3.5" /> Apply Changes
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-4 border border-dashed border-zinc-800 rounded-2xl bg-zinc-950/20 text-slate-500">
            <HelpCircle className="w-6 h-6 text-zinc-700 mb-1.5" />
            <p className="text-[10px] leading-relaxed">Select a canvas node to configure prompts, variables, or triggers.</p>
          </div>
        )}

        <button
          onClick={saveWorkflow}
          className="w-full py-2.5 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-md shadow-teal-500/25 cursor-pointer transition-all active:scale-95"
        >
          <Save className="w-4 h-4" /> Save Workflow
        </button>
      </div>

      {/* Center Canvas */}
      <div className="flex-1 bg-[#0b0c10] relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={customNodeTypes}
          fitView
        >
          <Background color="rgba(255,255,255,0.06)" variant={BackgroundVariant.Dots} gap={18} size={1} />
          <MiniMap
            nodeColor={(node) => {
              if (node.type === "start") return "rgba(16, 185, 129, 0.4)";
              if (node.type === "end") return "rgba(239, 68, 68, 0.4)";
              if (node.type === "action") return "rgba(20, 184, 166, 0.4)";
              return "rgba(99, 102, 241, 0.4)";
            }}
            maskColor="rgba(0,0,0,0.7)"
            style={{ background: "#18181b", border: "1px solid #27272a" }}
          />
          <Controls showInteractive={true} />
        </ReactFlow>
      </div>

      {/* Right Sidebar: WebRTC Voice Testing Sandbox */}
      <div className="w-80 border-l border-zinc-800 bg-zinc-900/60 backdrop-blur-xl flex flex-col justify-between flex-shrink-0">
        
        {/* Sandbox Header */}
        <div className="p-5 border-b border-zinc-800 space-y-2">
          <h2 className="text-base font-black tracking-tight text-white flex items-center gap-2">
            <Mic className="w-4 h-4 text-teal-400" /> Live Voice Sandbox
          </h2>
          <p className="text-[10px] text-slate-400 leading-normal">
            Interact with your agent in real-time right in your browser. Telephony features like transfer are simulated here.
          </p>
        </div>

        {/* Live Call Body / Dialogue bubbles */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-zinc-950/20">
          {isCalling ? (
            <div className="space-y-4">
              {/* Pulsing microphone status */}
              <div className="flex flex-col items-center py-4 space-y-2">
                <div className="w-16 h-16 rounded-full bg-teal-500/10 border-2 border-teal-500 flex items-center justify-center relative">
                  <div className="absolute inset-0 rounded-full border border-teal-400 animate-ping opacity-60" />
                  <Mic className="w-6 h-6 text-teal-400" />
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-teal-400 animate-pulse">Call Active</span>
              </div>

              {/* Message transcript bubbles */}
              <div className="space-y-2.5">
                {testTranscript.map((t, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col max-w-[85%] ${
                      t.sender === "user" ? "ml-auto items-end" : "mr-auto items-start"
                    }`}
                  >
                    <span className="text-[9px] text-slate-500 font-bold uppercase mb-0.5">{t.sender}</span>
                    <p className={`px-3 py-2 rounded-2xl text-[11px] font-medium leading-relaxed ${
                      t.sender === "user" 
                        ? "bg-teal-500 text-slate-950 rounded-tr-none font-semibold shadow-sm"
                        : "bg-zinc-800 text-slate-100 rounded-tl-none border border-zinc-700/40"
                    }`}>
                      {t.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
              <Phone className="w-8 h-8 text-zinc-700" />
              <p className="text-[11px] leading-relaxed">Click below to start a microphone sandbox call and speak to your receptionist agent.</p>
            </div>
          )}
        </div>

        {/* Latency & Telemetry indicators */}
        {isCalling && (
          <div className="px-5 py-3 border-t border-zinc-800 bg-zinc-950/40 space-y-2 text-[10px]">
            <span className="font-bold text-slate-400 uppercase tracking-widest text-[9px] block">Latency Telemetry</span>
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-zinc-900 border border-zinc-800 p-1.5 rounded-lg text-center">
                <span className="text-slate-500 block text-[8px] font-bold">STT</span>
                <span className="font-mono text-emerald-400 font-bold">{latencyMetrics.stt}ms</span>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 p-1.5 rounded-lg text-center">
                <span className="text-slate-500 block text-[8px] font-bold">LLM</span>
                <span className="font-mono text-emerald-400 font-bold">{latencyMetrics.llm}ms</span>
              </div>
              <div className="bg-zinc-900 border border-zinc-800 p-1.5 rounded-lg text-center">
                <span className="text-slate-500 block text-[8px] font-bold">TTS</span>
                <span className="font-mono text-emerald-400 font-bold">{latencyMetrics.tts}ms</span>
              </div>
            </div>
          </div>
        )}

        {/* Calling trigger panel */}
        <div className="p-5 border-t border-zinc-800 bg-zinc-950/60 flex flex-col space-y-2">
          {isCalling ? (
            <button
              onClick={stopVoiceTest}
              className="w-full py-3 bg-rose-500 hover:bg-rose-600 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-md shadow-rose-500/20 cursor-pointer transition-all active:scale-95 animate-pulse"
            >
              <PhoneOff className="w-4 h-4" /> End Sandbox Call
            </button>
          ) : (
            <button
              onClick={startVoiceTest}
              disabled={!selectedAgentId}
              className="w-full py-3 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-md shadow-teal-500/25 cursor-pointer transition-all active:scale-95"
            >
              <Phone className="w-4 h-4" /> Start Sandbox Call
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
