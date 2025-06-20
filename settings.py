from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class GlobalSettings(BaseSettings):
    app_name: str

    host_base_url: str

    cors: bool

    app_version: str

    mount_host: str

    # mqtt
    mqtt_broker: str

    mqtt_port: int

    mqtt_username: str

    mqtt_passwd: str

    mqtt_qos: int


global_settings = GlobalSettings()
