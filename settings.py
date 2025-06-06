from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class GlobalSettings(BaseSettings):
    app_name: str

    host_base_url: str

    cors: bool


global_settings = GlobalSettings()
