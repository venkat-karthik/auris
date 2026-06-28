import httpx
from loguru import logger
from typing import Any


class WorkflowGraphEngine:
    """
    Validates and executes visual conversation graphs.
    """

    @staticmethod
    def validate_graph(graph: dict) -> tuple[bool, str | None]:
        """
        Validates React Flow nodes and edges:
        - Exactly one start node.
        - Supported node types.
        - Basic cycle validation for webhooks.
        """
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not nodes:
            return True, None  # Empty graphs default to standard agent prompt

        # 1. Start node validation
        start_nodes = [n for n in nodes if n.get("type") == "startCall" or n.get("id") == "start"]
        if not start_nodes:
            return False, "Graph must have at least one 'startCall' entry node"
        if len(start_nodes) > 1:
            return False, "Graph cannot have multiple 'startCall' entry nodes"

        # 2. Node types validation
        valid_types = {"startCall", "agent", "webhook", "qa", "tuner", "endCall"}
        for node in nodes:
            ntype = node.get("type")
            if ntype and ntype not in valid_types:
                return False, f"Unsupported node type: {ntype} on node {node.get('id')}"

        # 3. Cycle validation (DFS checking for cycles in transitions)
        adj = {n["id"]: [] for n in nodes}
        for edge in edges:
            src = edge.get("source")
            dst = edge.get("target")
            if src in adj and dst in adj:
                adj[src].append(dst)

        visited = {}  # id -> state (0 = unvisited, 1 = visiting, 2 = visited)

        def has_cycle(u: str) -> bool:
            visited[u] = 1
            for v in adj.get(u, []):
                if visited.get(v, 0) == 1:
                    return True
                if visited.get(v, 0) == 0:
                    if has_cycle(v):
                        return True
            visited[u] = 2
            return False

        for node in nodes:
            nid = node["id"]
            if visited.get(nid, 0) == 0:
                if has_cycle(nid):
                    return False, f"Graph contains circular loops routing back to {nid}"

        return True, None


class WorkflowState:
    """
    Tracks runtime conversation state machine for an active call.
    """

    def __init__(self, graph: dict, context_variables: dict | None = None):
        self.graph = graph
        self.nodes = {n["id"]: n for n in graph.get("nodes", [])}
        self.edges = graph.get("edges", [])
        self.context = context_variables or {}
        self.active_node_id = self._find_start_node()
        self.history = []

    def _find_start_node(self) -> str | None:
        for nid, node in self.nodes.items():
            if node.get("type") == "startCall" or nid == "start":
                return nid
        return None

    def get_active_node(self) -> dict | None:
        if not self.active_node_id:
            return None
        return self.nodes.get(self.active_node_id)

    def transition_to_next(self, handle: str | None = None) -> dict | None:
        """
        Transition to the next node based on active node ID and edge handle.
        """
        if not self.active_node_id:
            return None

        # Find match edge
        target_node_id = None
        for edge in self.edges:
            if edge.get("source") == self.active_node_id:
                # If handle is specified, match sourceHandle
                if handle and edge.get("sourceHandle") != handle:
                    continue
                target_node_id = edge.get("target")
                break

        if target_node_id:
            self.history.append(self.active_node_id)
            self.active_node_id = target_node_id
            logger.info(f"Workflow transitioned to node: {target_node_id}")
            return self.nodes.get(target_node_id)
        
        logger.info(f"Workflow reached terminal state from node: {self.active_node_id}")
        return None

    async def execute_active_node(self, client: httpx.AsyncClient | None = None) -> tuple[str, bool]:
        """
        Executes active node logic:
        - For webhooks: runs external REST call, updates context variables, transitions to next.
        - Returns system prompt chunk and whether we should end the call.
        """
        node = self.get_active_node()
        if not node:
            return "", False

        ntype = node.get("type")
        ndata = node.get("data", {})

        if ntype == "startCall":
            # Just transition to next
            next_node = self.transition_to_next()
            if next_node:
                return await self.execute_active_node(client)
            return "", False

        elif ntype == "endCall":
            return "", True

        elif ntype == "webhook":
            url = ndata.get("url")
            method = ndata.get("method", "POST").upper()
            headers = ndata.get("headers", {})
            body_template = ndata.get("body", {})

            # Interpolate body values with context variables
            interpolated_body = {}
            for k, v in body_template.items():
                if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                    var_name = v[2:-2].strip()
                    interpolated_body[k] = self.context.get(var_name, "")
                else:
                    interpolated_body[k] = v

            logger.info(f"Webhook executing: {method} {url}")
            c = client or httpx.AsyncClient()
            try:
                if method == "POST":
                    resp = await c.post(url, json=interpolated_body, headers=headers, timeout=5.0)
                else:
                    resp = await c.get(url, params=interpolated_body, headers=headers, timeout=5.0)

                if resp.status_code >= 200 and resp.status_code < 300:
                    resp_data = resp.json()
                    # Merge response keys into context
                    if isinstance(resp_data, dict):
                        self.context.update(resp_data)
                    self.transition_to_next(handle="success")
                else:
                    logger.warning(f"Webhook failed with status {resp.status_code}")
                    self.transition_to_next(handle="fail")
            except Exception as e:
                logger.error(f"Webhook connection error: {e}")
                self.transition_to_next(handle="fail")

            # Re-execute the transitioned node
            return await self.execute_active_node(client)

        elif ntype == "qa":
            question = ndata.get("question", "")
            variable = ndata.get("expected_variable", "qa_ans")
            prompt = (
                f"Active Node (Question & Answer): {node['id']}\n"
                f"You MUST ask the user this exact question: '{question}'\n"
                f"Once they reply, parse and extract the answer for key: '{variable}' and trigger variable update.\n"
            )
            return prompt, False

        elif ntype == "tuner":
            # Update settings in context
            props = ndata.get("properties", {})
            self.context.update(props)
            self.transition_to_next()
            return await self.execute_active_node(client)

        # Standard agent node
        prompt = ndata.get("system_prompt", "")
        return prompt, False
