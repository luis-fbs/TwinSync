import logging
import sys
import threading

import common
from twinsync import TwinSync

logging.basicConfig(level=logging.INFO)

scenario = common.scenario_from_args()
if scenario == "twinsync_tls":
    tls = {"port": common.TLS_PORT}
elif scenario == "twinsync_mtls":
    tls = {"port": common.MTLS_PORT, "certfile": common.DT_CERT, "keyfile": common.DT_KEY}
else:
    sys.exit("dt_twinsync.py is only used in the twinsync_tls and twinsync_mtls scenarios")

twin = TwinSync(
    TwinSync.DIGITAL_TWIN,
    host=common.BROKER_HOST,
    ca_certs=common.CA_CERT,
    username=common.USERNAME,
    password=common.PASSWORD,
    qos=common.QOS,
    **tls,
)
twin.start()
print("TwinSync running (Ctrl+C to stop)")
threading.Event().wait()
