import unittest

from mcp4hal.hub import McpServerRegistryManager, McpToolRegistryManager


class TestRegistry(unittest.TestCase):
    """测试注册表"""
    
    def test_registry(self):
        config_path = '/Users/manson/ai/app/physical_agent/mcp4hal/config/mcp_servers_config.json'

        mcp_servers = McpServerRegistryManager.load_mcp_servers(config_path=config_path)
        print(mcp_servers)

        mcp_tools = McpToolRegistryManager.load_mcp_tools(mcp_servers=mcp_servers)
        print(mcp_tools)

if __name__ == '__main__':
    unittest.main()
