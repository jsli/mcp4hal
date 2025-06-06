from core.server_base import McpServerBase


class MockMcpServerSse(McpServerBase):

    name = 'MockMcpServerSse'

    description = 'MockMcpServerSse Service'

    server_type = 'sse'

    @staticmethod
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    @staticmethod
    def sub(a: int, b: int) -> int:
        """Sub two numbers"""
        return a - b

    @staticmethod
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers"""
        return a * b


class MockMcpServerHttpStreamable(McpServerBase):

    name = 'MockMcpServerHttpStreamable'

    description = 'MockMcpServerHttpStreamable Service'

    server_type = 'streamable_http'

    @staticmethod
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    @staticmethod
    def sub(a: int, b: int) -> int:
        """Sub two numbers"""
        return a - b

    @staticmethod
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers"""
        return a * b
