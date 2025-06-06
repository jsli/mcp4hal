import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from mock.mock_mcp_server import MockMcpServerHttpStreamable, MockMcpServerSse
from settings import global_settings

_settings = global_settings


def init_mcp_servers(_app: FastAPI):
    mcp_servers = {}
    base_url = _settings.host_base_url

    sse_server = MockMcpServerSse.mount(app=app, base_url=base_url, mount_path='/mcp/sse/')
    mcp_servers[sse_server.name] = sse_server

    streamable_http_server = MockMcpServerHttpStreamable.mount(app=app, base_url=base_url, mount_path='/mcp/streamable_http/')
    mcp_servers[streamable_http_server.name] = streamable_http_server

    return [sse_server, streamable_http_server]


def create_app(run_mode: str = None, lifespan = None):
    _app = FastAPI(title='MCP4HAL', version='0.0.1', lifespan=lifespan)
    if _settings.cors:
        _app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    return _app


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastApi服务启动")
    mcp_servers = init_mcp_servers(_app=app)
    async with contextlib.AsyncExitStack() as stack:
        for server in mcp_servers:
            if server.server_type == 'streamable_http':
                # Create a combined lifespan to manage both session managers
                await stack.enter_async_context(server.mcp_server.session_manager.run())
        yield
    print("FastApi服务关闭")


app = create_app(lifespan=lifespan)


@app.get("/", summary="swagger 文档", include_in_schema=False)
async def document():
    return RedirectResponse(url="/docs")
