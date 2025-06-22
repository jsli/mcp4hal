import time

import machine
import network
from umqtt.simple import MQTTClient

# WiFi配置
WIFI_SSID = "ZJJYJ"
WIFI_PASS = "qwert123"

# MQTT配置
MQTT_SERVER = "192.168.152.224"  # 公共测试服务器
MQTT_QOS=1
MQTT_PORT=1883
MQTT_CLIENT_ID = "esp32_" + str(machine.unique_id())[-4:]
MQTT_TOPIC_PUB = "esp32/pub"  # 发布主题
MQTT_TOPIC_SUB = "esp32/sub"  # 订阅主题
MQTT_USERNAME='mqtt_dev'
MQTT_PASSWD='abcd1234'
CLIENT_ID = "micropython_" + str(machine.unique_id())[-4:]  # 唯一客户端ID
client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_SERVER, port=MQTT_PORT, user=MQTT_USERNAME, password=MQTT_PASSWD)


# 连接WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("正在连接WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(1)
    print("WiFi已连接:", wlan.ifconfig())


# 消息回调函数
def on_message(topic, msg):
    print(f"收到消息: Topic={topic.decode()}, Message={msg.decode()}")
    client.publish(MQTT_TOPIC_PUB, msg)


# 主函数
def main():
    connect_wifi()

    # 初始化MQTT客户端
    # client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, MQTT_USERNAME, MQTT_PASSWD)

    client.set_callback(on_message)
    client.run()
    client.subscribe(MQTT_TOPIC_SUB)
    print(f"已连接到MQTT服务器: {MQTT_SERVER}")

    # 主循环
    counter = 0
    try:
        while True:
            # 发布消息
            msg = f"Hello {counter}"
            client.publish(MQTT_TOPIC_PUB, msg)
            print(f"已发布: {msg}")
            counter += 1

            # 检查订阅消息（非阻塞）
            # client.check_msg()
            client.wait_msg()
            # time.sleep(3)

    except KeyboardInterrupt:
        print("断开连接...")
        client.disconnect()


# 启动
main()
