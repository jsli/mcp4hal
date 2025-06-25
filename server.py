from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse

from core.protocol.mqtt_schema import MqttBrokerConnectionConfig
from hal.mqtt import McpServerProxyMqttSupervisor
from settings import global_settings


def init_mcp_servers(_app: FastAPI):
    connection_config = MqttBrokerConnectionConfig(
        client_id=global_settings.app_name.lower(),
        username=global_settings.mqtt_username,
        passwd=global_settings.mqtt_passwd,
        broker=global_settings.mqtt_broker,
        port=global_settings.mqtt_port,
        qos=global_settings.mqtt_qos,
    )
    supervisor = McpServerProxyMqttSupervisor(connection_config=connection_config, mount_host=global_settings.mount_host)
    _app.state.mcp_server_mqtt_supervisor = supervisor
    supervisor.start(daemon=False)
    return supervisor.get_mcp_servers()


def create_app(run_mode: str = None, lifespan = None):
    _app = FastAPI(title=global_settings.app_name, version=global_settings.app_version, lifespan=lifespan)
    if global_settings.cors:
        _app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    return _app


app = create_app()
init_mcp_servers(_app=app)


@app.get("/list/servers", summary="获取mcp server列表", include_in_schema=False)
async def list_mcp_servers(request: Request):
    data = request.app.state.mcp_server_mqtt_supervisor.get_mcp_servers()
    return JSONResponse(content=data)


@app.get("/", summary="swagger 文档", include_in_schema=False)
async def document():
    return RedirectResponse(url="/docs")
