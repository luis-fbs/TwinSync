# luis-fbs

"""TwinSync: secure synchronization channel between a physical entity and its digital twin.
"""

import functools
import json
import logging
import ssl
import threading
import time
from collections import defaultdict
from collections.abc import Mapping

import paho.mqtt.client as mqtt

logger = logging.getLogger("twinsync")


class TwinSync:
    # Synchronization types
    SYNC = "sync"
    ASYNC = "async"

    # Sides of the digital twin
    PHYSICAL_ENTITY = "physical_entity"
    DIGITAL_TWIN = "digital_twin"

    # Values of the "sync" key added to delivered messages
    SYNC_KEY = "sync"
    SYNCHRONIZED = "synchronized"
    DESYNCHRONIZED = "desynchronized"

    # Control message asking the other side for resync
    RESYNC_REQUEST = "resync_request"

    DEFAULT_MAX_DEVIATION = 0.05  # seconds
    DEFAULT_PORT = 8883

    def __init__(
        self,
        side,
        host="localhost",
        port=DEFAULT_PORT,
        ca_certs=None,
        certfile=None,
        keyfile=None,
        max_deviation=DEFAULT_MAX_DEVIATION,
        qos=1,
        username=None,
        password=None,
        topic_prefix="twinsync",
        client_id=None,
    ):
        """
        :param side: `TwinSync.PHYSICAL_ENTITY` or `TwinSync.DIGITAL_TWIN`.
        :param host: MQTT broker host.
        :param port: MQTT broker TLS port.
        :param ca_certs: CA bundle used to validate the broker certificate
        :param certfile: optional client certificate (mutual TLS).
        :param keyfile: optional client private key (mutual TLS).
        :param max_deviation: maximum accepted difference, in seconds, between
            the send and arrival times of a synchronous message.
        :param qos: MQTT QoS used for every publication.
        :param topic_prefix: prefix of the topics used between both TwinSync
            instances. Both sides of a twin must use the same prefix.
        """

        if side not in (self.PHYSICAL_ENTITY, self.DIGITAL_TWIN):
            raise ValueError(f"Invalid side {side!r}")
        if max_deviation <= 0:
            raise ValueError("max_deviation must be positive")

        self.side = side
        self.max_deviation = max_deviation
        self.qos = qos
        self.host = host
        self.port = port

        peer = self.DIGITAL_TWIN if side == self.PHYSICAL_ENTITY else self.PHYSICAL_ENTITY
        self.inbox_topic = f"{topic_prefix}/{side}"
        self.peer_topic = f"{topic_prefix}/{peer}"

        self._handlers = defaultdict(list)
        self._resync_handlers = {}
        self._connected = threading.Event()

        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id or f"{topic_prefix}-{side}",
            clean_session=False,
        )
        self._client.tls_set(
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT,
        )
        if username is not None:
            self._client.username_pw_set(username, password)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.message_callback_add(self.inbox_topic, self._on_inbox_message)

    # Lifecycle
    def start(self, timeout=10):
        """Connect to the broker and wait until the inbox is subscribed."""
        self._client.connect_async(self.host, self.port)
        self._client.loop_start()
        if not self._connected.wait(timeout):
            self._client.loop_stop()
            raise ConnectionError(f"Could not connect to {self.host}:{self.port} within {timeout}s")
        return self

    def stop(self):
        self._client.disconnect()
        self._client.loop_stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error(f"Connection refused by broker: {reason_code}")
            return
        client.subscribe(self.inbox_topic, qos=self.qos)
        logger.info(f"[{self.side}] connected, listening on {self.inbox_topic}")
        self._connected.set()

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self._connected.clear()
        if reason_code != 0:
            logger.warning(f"[{self.side}] disconnected: {reason_code}")

    # Decorators
    def publish(self, target_topic, sync_type):
        """Decorator: securely sends the dict returned by the function to `target_topic`,
        according to the selected `sync_type`.
        """
        self._check_sync_type(sync_type)

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                payload = func(*args, **kwargs)
                self.send(target_topic, payload, sync_type)
                return payload

            return wrapper

        return decorator

    def subscribe(self, target_topic):
        """Decorator (physical entity side): receive messages sent to `target_topic`.

        If message arrived too late it receives only `{"sync": "desynchronized"}`.
        """
        if self.side != self.PHYSICAL_ENTITY:
            raise RuntimeError(
                "subscribe() is only available on the physical entity side; "
                "the digital twin side delivers messages to the broker topic"
            )

        def decorator(func):
            self._handlers[target_topic].append(func)
            return func

        return decorator

    def on_resync(self, target_topic):
        """Decorator: function called when a message sent to `target_topic` arrived too late.

        The late message was discarded by the other side. The function decides what to
        send instead, using the normal publish functions: the physical entity usually
        sends its current state; the digital twin sends a new command, or nothing if
        the command is no longer wanted.
        """
        def decorator(func):
            self._resync_handlers[target_topic] = func
            return func

        return decorator

    # Sending
    def send(self, target_topic, payload, sync_type):
        """Wrap `payload` in an envelope and send it to the TwinSync counterpart."""
        self._check_sync_type(sync_type)
        if not isinstance(payload, Mapping):
            raise TypeError(f"Payload for {target_topic!r} must be a dict, got {type(payload).__name__}")

        envelope = {"target_topic": target_topic, "type": sync_type, "payload": dict(payload)}
        if sync_type == self.SYNC:
            envelope["timestamp"] = time.time()
        self._publish(self.peer_topic, envelope)

    def _publish(self, topic, message):
        info = self._client.publish(topic, json.dumps(message), qos=self.qos)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Failed to publish to {topic}: {mqtt.error_string(info.rc)}")

    def _check_sync_type(self, sync_type):
        if sync_type not in (self.SYNC, self.ASYNC):
            raise ValueError(f"Invalid sync type {sync_type!r}; use TwinSync.SYNC or TwinSync.ASYNC")

    # Receiving
    def _on_inbox_message(self, client, userdata, msg):
        self._handle_envelope(msg.payload, received_at=time.time())

    def _handle_envelope(self, raw, received_at):
        try:
            envelope = json.loads(raw)
            if not isinstance(envelope, dict):
                raise TypeError("envelope is not an object")
            if "control" in envelope:
                self._handle_control(envelope)
                return
            target_topic = envelope["target_topic"]
            sync_type = envelope["type"]
            payload = envelope["payload"]
            if not isinstance(payload, dict):
                raise TypeError("payload is not an object")
            sent_at = float(envelope["timestamp"]) if sync_type == self.SYNC else None
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning(f"Discarding malformed envelope {raw!r}: {exc}")
            return

        if sync_type == self.ASYNC:
            self._deliver(target_topic, {**payload, self.SYNC_KEY: self.SYNCHRONIZED})
        elif sync_type == self.SYNC:
            deviation = received_at - sent_at
            if abs(deviation) <= self.max_deviation:
                self._deliver(target_topic, {**payload, self.SYNC_KEY: self.SYNCHRONIZED})
            else:
                logger.warning(
                    f"[{self.side}] {target_topic} desynchronized: "
                    f"deviation {deviation:.3f}s > {self.max_deviation:.3f}s"
                )
                self._deliver(target_topic, {self.SYNC_KEY: self.DESYNCHRONIZED})
                self._request_resync(target_topic)
        else:
            logger.warning(f"Discarding envelope with unknown type {sync_type!r}")

    def _deliver(self, target_topic, message):
        if self.side == self.DIGITAL_TWIN:
            self._publish(target_topic, message)
            return

        handlers = self._handlers.get(target_topic)
        if not handlers:
            logger.warning(f"[{self.side}] no handler subscribed to {target_topic}; message dropped")
            return
        for handler in handlers:
            try:
                handler(message)
            except Exception:
                logger.exception(f"Handler {handler.__name__} failed for {target_topic}")

    # Resynchronization
    def _request_resync(self, target_topic):
        self._publish(self.peer_topic, {"control": self.RESYNC_REQUEST, "target_topic": target_topic})

    def _handle_control(self, envelope):
        if envelope.get("control") != self.RESYNC_REQUEST:
            logger.warning(f"Discarding unknown control message {envelope!r}")
            return
        target_topic = envelope.get("target_topic")
        handler = self._resync_handlers.get(target_topic)
        if handler is None:
            logger.warning(f"[{self.side}] resync requested for {target_topic}, but no on_resync handler")
            return
        logger.info(f"[{self.side}] resync requested for {target_topic}")
        try:
            handler()
        except Exception:
            logger.exception(f"Resync handler {handler.__name__} failed for {target_topic}")
