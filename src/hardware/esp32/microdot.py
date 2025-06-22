from microdot import Microdot, Response
import json
import network
import machine

app = Microdot()
Response.default_content_type = 'application/json'

# MCP 协议版本和基础配置
MCP_VERSION = "2025-06-18"
SERVER_CAPABILITIES = {
    "jsonrpc": "2.0",
    "capabilities": {
        "tools": {
            "dynamicRegistration": False,
            "listChanged": False
        }
    }
}

# 工具定义
TOOLS = {
    "math/add": {
        "name": "math/add",
        "title": "Addition Tool",
        "description": "Performs addition of two numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First operand"},
                "b": {"type": "number", "description": "Second operand"}
            },
            "required": ["a", "b"]
        }
    }
}


# MCP 协议端点
@app.route('/.well-known/mcp', methods=['GET'])
def get_mcp_info(request):
    """返回 MCP 协议描述"""
    return {
        "version": MCP_VERSION,
        "capabilities": SERVER_CAPABILITIES
    }


@app.route('/tools/list', methods=['GET'])
def list_tools(request):
    """列出可用工具"""
    return {
        "tools": [{
            "name": tool["name"],
            "title": tool["title"],
            "description": tool["description"]
        } for tool in TOOLS.values()]
    }


@app.route('/tools/execute', methods=['POST'])
def execute_tool(request):
    """执行工具调用"""
    try:
        data = json.loads(request.body.decode())

        # 验证 JSON-RPC 2.0 基本结构
        if data.get("jsonrpc") != "2.0" or "method" not in data:
            return {"error": "Invalid JSON-RPC 2.0 request"}, 400

        # 检查工具是否存在
        if data["method"] not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": "Method not found"
                },
                "id": data.get("id")
            }, 404

        # 执行加法工具
        if data["method"] == "math/add":
            params = data.get("params", {})
            if not all(k in params for k in ['a', 'b']):
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32602,
                        "message": "Invalid params"
                    },
                    "id": data.get("id")
                }, 400

            result = params['a'] + params['b']
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{
                        "type": "text",
                        "text": str(result)
                    }],
                    "outputSchema": {
                        "type": "number",
                        "description": "Sum of a and b"
                    }
                },
                "id": data.get("id")
            }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            },
            "id": data.get("id", None)
        }, 500


# WiFi 连接
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('Network config:', wlan.ifconfig())


# 启动服务器
def run_server():
    connect_wifi('YOUR_SSID', 'YOUR_PASSWORD')
    print('MCP Server running on:', network.WLAN(network.STA_IF).ifconfig()[0])
    app.run(port=80)


if __name__ == '__main__':
    run_server()
