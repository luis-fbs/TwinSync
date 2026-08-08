from time import time

MQTT_HOST = "192.168.3.10"
MQTT_PORT = 1883
MQTT_TOPIC = "robotic-arm"

DITTO_URL = "http://localhost:8080"
DITTO_WS = "ws://localhost:8080/ws/2"
DITTO_AUTH = ("ditto", "ditto")
DITTO_DEVOPS_AUTH = ("devops", "foobar")

NAMESPACE = "dt"
THING_NAME = "robotic-arm"
THING_ID = f"{NAMESPACE}:{THING_NAME}"

OWNER_SUBJECT = "nginx:ditto"
CONN_SUBJECT = "ditto:roboticArm"

POLICY = {
    "entries": {
        "owner": {
            "subjects": {OWNER_SUBJECT: {"type": "iot-user"}},
            "resources": {
                "thing:/": {"grant": ["READ", "WRITE"], "revoke": []},
                "policy:/": {"grant": ["READ", "WRITE"], "revoke": []},
                "message:/": {"grant": ["READ", "WRITE"], "revoke": []},
            },
        },
        "connection": {
            "subjects": {CONN_SUBJECT: {"type": "connection"}},
            "resources": {
                "thing:/": {"grant": ["READ", "WRITE"], "revoke": []},
                "message:/": {"grant": ["READ", "WRITE"], "revoke": []},
            },
        },
    }
}

THING = {
    "policyId": THING_ID,
    "attributes": {
        "name": "Robotic Arm",
        "pin": 18,
        "minAngle": 0,
        "maxAngle": 180,
    },
    "features": {
        "angle": {"properties": {"value": 90}},
        "timestamp": {"properties": {"value": time()}},
        "safe": {"properties": {"value": True}},
    },
}

CONNECTION = {
    "name": "MQTT 5",
    "connectionType": "mqtt-5",
    "connectionStatus": "open",
    "failoverEnabled": True,
    "uri": f"tcp://{MQTT_HOST}:{MQTT_PORT}",
    "sources": [
        {
            "addresses": [MQTT_TOPIC],
            "authorizationContext": [CONN_SUBJECT],
            "payloadMapping": ["Ditto"],
            "qos": 0,
        }
    ],
    "targets": [],
}

