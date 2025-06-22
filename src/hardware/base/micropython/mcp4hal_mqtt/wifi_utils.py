import network
import time

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        print("WiFi已连接:", wlan.ifconfig())
        return True

    wlan.active(True)
    if not wlan.isconnected():
        print(f"正在连接WiFi...{ssid} - {password}")
        wlan.connect(ssid, password)
        timeout = 30  # 设置连接超时时间为 30 秒
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                print("WiFi connection timeout!")
                return False
            try:
                print("Trying to connect...")
                wlan.connect(ssid, password)
                time.sleep(1)
            except Exception as e:
                print(f"Error connecting to WiFi: {e}")
                return False
    print("WiFi已连接:", wlan.ifconfig())
    return True
