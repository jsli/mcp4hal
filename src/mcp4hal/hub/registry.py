import asyncio

from langchain_mcp_adapters.sessions import create_session
from mcp.types import Tool
from pydantic import BaseModel


class McpServerModel(BaseModel):
    transport: str

    url: str

    name: str

    description: str


class McpServerRegistryManager:

    mcp_servers: list

    config_path: str

    @classmethod
    def load_mcp_servers(cls, config_path: str):
        registry = cls(config_path=config_path)
        return registry.get_mcp_servers()

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._load_config()

    def _load_config(self):
        try:
            import json
            with open(self.config_path, 'r') as f:
                mcp_servers = json.load(f)
                self.mcp_servers = []
                for item in mcp_servers:
                    self.mcp_servers.append(McpServerModel(**item))
        except Exception as e:
            pass

    def get_mcp_servers(self):
        return self.mcp_servers


class McpToolRegistryManager:

    mcp_tools: list[Tool]

    @classmethod
    def load_mcp_tools(cls, mcp_servers: list[McpServerModel]):
        registry = cls()
        asyncio.run(registry.fetch_mcp_tools_async(mcp_servers=mcp_servers))
        return registry.get_mcp_tools()

    def __init__(self):
        self.mcp_tools = []

    async def fetch_mcp_tools_async(self, mcp_servers: list[McpServerModel]):
        self.mcp_tools = []
        for mcp_server in mcp_servers:
            connection = {
                "transport": mcp_server.transport,
                "url": mcp_server.url,
            }
            async with create_session(connection) as tool_session:
                await tool_session.initialize()
                tools = await tool_session.list_tools()
                self.mcp_tools.extend(tools.tools)

    def fetch_mcp_tools(self, mcp_servers: list[McpServerModel]):
        return asyncio.run(self.fetch_mcp_tools_async(mcp_servers=mcp_servers))

    def get_mcp_tools(self):
        return self.mcp_tools
