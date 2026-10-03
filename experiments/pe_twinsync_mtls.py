import common
from twinsync import TwinSync

twin = TwinSync(
    TwinSync.PHYSICAL_ENTITY,
    host=common.BROKER_HOST,
    port=common.MTLS_PORT,
    ca_certs=common.CA_CERT,
    certfile=common.PE_CERT,
    keyfile=common.PE_KEY,
    username=common.USERNAME,
    password=common.PASSWORD,
    qos=common.QOS,
)
twin.start()


@twin.publish(common.TOPIC, TwinSync.SYNC)
def send(message):
    return message


common.send_messages(send)
twin.stop()
