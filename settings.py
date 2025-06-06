from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class GlobalSettings(BaseSettings):
    app_name: str

    host_base_url: str

    cors: bool

    mcp_server_config_path: str


global_settings = GlobalSettings()
