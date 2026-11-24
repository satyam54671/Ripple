"""MCP Client wrapper dispatching tool calls through the RIPPLE MCPServer."""

import json
from typing import Any, Dict, List
from mcp.server.mcpserver import MCPServer

from app.integrations.mcp.server import ripple_mcp_server


class RippleMCPClient:
    """
    Client interface used by RIPPLE agents to discover and invoke MCP tools.
    Calls execute directly against MCPServer's tool registry so every tool
    interaction follows MCP schema validation and structured result handling.
    """

    def __init__(self, server: MCPServer | None = None):
        self.server = server or ripple_mcp_server

    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """Discover registered MCP tools and their schemas."""
        tools = await self.server.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": getattr(tool, "input_schema", getattr(tool, "inputSchema", {})),
            }
            for tool in tools
        ]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a named MCP tool and normalize the structured JSON response."""
        result = await self.server.call_tool(tool_name, arguments)

        # mcp 2.x returns CallToolResult(content=..., structured_content=...)
        structured = getattr(result, "structured_content", None)
        if isinstance(structured, dict) and "result" in structured:
            return structured["result"]
        if structured is not None:
            return structured

        content = getattr(result, "content", result)
        if isinstance(content, tuple) and len(content) == 2:
            content_blocks, structured_tuple = content
            if isinstance(structured_tuple, dict) and "result" in structured_tuple:
                return structured_tuple["result"]
            if structured_tuple is not None:
                return structured_tuple
            content = content_blocks

        if isinstance(content, list) and content:
            texts = [getattr(block, "text", None) for block in content if getattr(block, "text", None)]
            if len(texts) == 1:
                try:
                    return json.loads(texts[0])
                except json.JSONDecodeError:
                    return texts[0]
            if len(texts) > 1:
                parsed = []
                for t in texts:
                    try:
                        parsed.append(json.loads(t))
                    except json.JSONDecodeError:
                        parsed.append(t)
                return parsed
        return content
