# @auris/mcp-server (`auris-mcp-server`)

Standalone Model Context Protocol (MCP) server for the **Auris Enterprise Voice AI Platform**. Use this server with local AI clients like **Claude Desktop**, **Cursor**, or **Windsurf** to build, inspect, and deploy voice AI agents directly from your editor or chat window.

---

## 📦 Installation

```bash
cd sdk/mcp-server
pip install -e .
```

---

## ⚙️ Configuration for Claude Desktop / Cursor

Add the following to your `claude_desktop_config.json` or Cursor MCP settings:

```json
{
  "mcpServers": {
    "auris": {
      "command": "python",
      "args": ["-m", "auris_mcp_server.main"],
      "env": {
        "AURIS_API_KEY": "<your_auris_api_key>",
        "AURIS_BASE_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

---

## 🛠️ Available Tools

1. `dispatch_a_call(agent_id, to_number, call_context)`: Initiate an outbound voice call.
2. `create_assistant(name, system_prompt, welcome_message)`: Create a new virtual voice agent.
3. `start_campaign(campaign_id)`: Start an outbound dialer campaign.
4. `get_balance()`: Check your organization's Razorpay credit balance.

---

## 📄 License
MIT License © Auris Voice AI Platform
