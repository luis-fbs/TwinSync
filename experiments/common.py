import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Network
BROKER_HOST = "192.168.0.10"
PE_HOST = "192.168.0.11"
SOCKET_PORT = 5000

# Broker
MQTT_PORT = 1883
TLS_PORT = 8883
MTLS_PORT = 8884
USERNAME = "twin"
PASSWORD = "twin-pass"
QOS = 1
TOPIC = "experiment/data"

# Certificates
CERTS = ROOT / "certs"
CA_CERT = str(CERTS / "ca.crt")
PE_CERT, PE_KEY = str(CERTS / "physical_entity.crt"), str(CERTS / "physical_entity.key")
DT_CERT, DT_KEY = str(CERTS / "digital_twin.crt"), str(CERTS / "digital_twin.key")

# Experiment
N_MESSAGES = 10000
RATE_HZ = 10
SCENARIOS = ("mqtt", "mqtt_tls", "twinsync_tls", "twinsync_mtls")
RESULTS = Path(__file__).resolve().parent / "results"


def scenario_from_args():
    if len(sys.argv) != 2 or sys.argv[1] not in SCENARIOS:
        sys.exit(f"usage: python {sys.argv[0]} {{{'|'.join(SCENARIOS)}}}")
    return sys.argv[1]


def send_messages(send):
    for seq in range(N_MESSAGES):
        send({"seq": seq, "timestamp": time.time()})
        time.sleep(0.1)
    print(f"sent {N_MESSAGES} messages")


def connect(client, port, timeout=10):
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKER_HOST, port)
    client.loop_start()
    deadline = time.time() + timeout
    while not client.is_connected():
        if time.time() > deadline:
            sys.exit(f"could not connect to {BROKER_HOST}:{port} (check address, certificates and credentials)")
        time.sleep(0.1)
