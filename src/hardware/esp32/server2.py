import json

import asyncio as asyncio


class StreamingHTTPServer:
    def __init__(self, host='0.0.0.0', port=80):
        self.host = host
        self.port = port
        self.routes = {}
        self.chunk_size = 1024  # 默认块大小

    def route(self, path, methods=['GET']):
        def decorator(handler):
            self.routes[(path, tuple(methods))] = handler
            return handler

        return decorator

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"Streaming HTTP server running on http://{self.host}:{self.port}")
        await server.wait_closed()

    async def handle_client(self, reader, writer):
        try:
            # 解析请求行
            request_line = await reader.readline()
            method, path, proto = self.parse_request_line(request_line)

            # 解析请求头
            headers = {}
            while True:
                line = await reader.readline()
                if line == b'\r\n' or line == b'':
                    break
                key, value = line.decode().strip().split(': ', 1)
                headers[key] = value

            # 查找匹配的路由
            handler = None
            for (route_path, methods), route_handler in self.routes.items():
                if method in methods and self.path_matches(route_path, path):
                    handler = route_handler
                    break

            if handler:
                # 调用处理函数
                response = await handler(Request(method, path, headers, reader))

                # 写入响应
                if isinstance(response, StreamingResponse):
                    await self.send_streaming_response(writer, response)
                else:
                    await self.send_regular_response(writer, response)
            else:
                await self.send_404(writer)

        except Exception as e:
            print("Error handling request:", e)
            await self.send_500(writer)
        finally:
            await writer.drain()
            writer.close()
            await writer.wait_closed()

    async def send_streaming_response(self, writer, response):
        # 写入状态行和头
        writer.write(f"HTTP/1.1 {response.status_code} {response.reason}\r\n".encode(encoding="utf-8"))
        for header, value in response.headers.items():
            writer.write(f"{header}: {value}\r\n".encode(encoding="utf-8"))
        writer.write("\r\n".encode(encoding="utf-8"))
        await writer.drain()

        # 流式传输内容
        async for chunk in response.stream():
            if isinstance(chunk, str):
                chunk = chunk.encode('utf-8')
            writer.write(f"{len(chunk):X}\r\n".encode(encoding="utf-8") + chunk + b"\r\n")
            await writer.drain()

        # 结束块传输
        writer.write(b"0\r\n\r\n")
        await writer.drain()

    async def send_regular_response(self, writer, response):
        if isinstance(response, tuple):
            status_code, content, headers = response
        else:
            status_code, content, headers = 200, response, {}

        if isinstance(content, str):
            content = content.encode('utf-8')

        writer.write(f"HTTP/1.1 {status_code} OK\r\n")
        writer.write(f"Content-Length: {len(content)}\r\n")
        for header, value in headers.items():
            writer.write(f"{header}: {value}\r\n")
        writer.write("\r\n")
        writer.write(content)
        await writer.drain()

    async def send_404(self, writer):
        await self.send_regular_response(writer, (
            404, "Not Found", {"Content-Type": "text/plain"}
        ))

    async def send_500(self, writer):
        await self.send_regular_response(writer, (
            500, "Internal Server Error", {"Content-Type": "text/plain"}
        ))

    def parse_request_line(self, line):
        parts = line.decode().strip().split()
        return parts[0], parts[1], parts[2]

    def path_matches(self, pattern, path):
        if pattern == path:
            return True
        # 简单通配符匹配
        if pattern.endswith('*'):
            return path.startswith(pattern[:-1])
        return False


class Request:
    def __init__(self, method, path, headers, reader):
        self.method = method
        self.path = path
        self.headers = headers
        self.reader = reader


class StreamingResponse:
    def __init__(self, stream, status_code=200, reason="OK", headers=None):
        self.stream = stream
        self.status_code = status_code
        self.reason = reason
        self.headers = headers or {}
        self.headers["Transfer-Encoding"] = "chunked"

    async def __aiter__(self):
        stream = self.stream() if callable(self.stream) else self.stream
        async for chunk in stream:
            yield chunk


async def file_chunker(filename, chunk_size=1024):
    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


async def sensor_data_stream():
    import time
    import random
    while True:
        data = {
            "timestamp": time.time(),
            "value": random.randint(0, 100)
        }
        yield json.dumps(data) + "\n"
        await asyncio.sleep(1)


def sensor_data_producer():
    return sensor_data_stream()


# 使用示例
async def main():
    server = StreamingHTTPServer()

    @server.route('/')
    async def home(request):
        return "Welcome to the Streaming MicroPython Server!"

    @server.route('/stream')
    async def stream_data(request):
        return StreamingResponse(sensor_data_producer, headers={
            "Content-Type": "application/json"
        })

    @server.route('/file')
    async def stream_file(request):
        filename = "largefile.bin"  # 替换为实际文件
        return StreamingResponse(file_chunker(filename), headers={
            "Content-Type": "application/octet-stream"
        })

    await server.start()


# asyncio.run(main())
asyncio.run(sensor_data_stream())