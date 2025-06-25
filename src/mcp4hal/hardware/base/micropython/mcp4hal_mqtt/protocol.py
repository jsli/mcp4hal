# mqtt_const.py copy

MQTT_TOPIC_PREFIX = 'mcp4hal'

MCP4HAL_MQTT_TOPIC_REGISTER_F = f'{MQTT_TOPIC_PREFIX}/%s/register'
MCP4HAL_MQTT_TOPIC_REGISTER = f'{MQTT_TOPIC_PREFIX}/+/register'
'''mqtt client注册为mcp server的topic, client->hal'''


MCP4HAL_MQTT_TOPIC_UNREGISTER_F = f'{MQTT_TOPIC_PREFIX}/%s/unregister'
MCP4HAL_MQTT_TOPIC_UNREGISTER = f'{MQTT_TOPIC_PREFIX}/+/unregister'
'''mqtt client注销mcp server的topic, client->hal'''


MCP4HAL_MQTT_TOPIC_WILL_F = MCP4HAL_MQTT_TOPIC_UNREGISTER_F
MCP4HAL_MQTT_TOPIC_WILL = MCP4HAL_MQTT_TOPIC_UNREGISTER
'''mqtt client的遗嘱消息，注销'''


MCP4HAL_MQTT_TOPIC_TOOLCALL_F = f'{MQTT_TOPIC_PREFIX}/%s/tc'
MCP4HAL_MQTT_TOPIC_TOOLCALL = f'{MQTT_TOPIC_PREFIX}/+/tc'
'''mqtt client订阅接收tool call的topic, client<-hal'''


MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F = f'{MQTT_TOPIC_PREFIX}/%s/tcr'
MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT = f'{MQTT_TOPIC_PREFIX}/+/tcr'
'''mqtt client发布toolcall result topic, client->hal'''


MCP4HAL_MQTT_QOS = 1
'''mqtt qos, 送达1次，消息不会丢失，可能会重复'''
