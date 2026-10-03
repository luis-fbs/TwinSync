import json
import socket
import time

import common

scenario = common.scenario_from_args()
latencies = []
desynchronized = 0

with socket.create_server(("0.0.0.0", common.SOCKET_PORT)) as server:
    print(f"waiting for the digital twin on port {common.SOCKET_PORT}...")
    conn, address = server.accept()
    print(f"digital twin connected from {address[0]}, waiting for {common.N_MESSAGES} messages")
    with conn, conn.makefile("rb") as stream:
        for line in stream:
            now = time.time()
            message = json.loads(line)
            if "timestamp" in message:
                latencies.append(now - message["timestamp"])
            else:  # TwinSync discarded a late message: {"sync": "desynchronized"}
                desynchronized += 1
            if len(latencies) + desynchronized == common.N_MESSAGES:
                break

common.RESULTS.mkdir(exist_ok=True)
output = common.RESULTS / f"{scenario}.txt"
output.write_text("".join(f"{latency}\n" for latency in latencies))
print(f"{len(latencies)} latencies saved to {output} ({desynchronized} desynchronized)")
