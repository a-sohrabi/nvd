from confluent_kafka import Producer

from .config import settings
from .logger import logger


class KafkaProducer:
    def __init__(self, config):
        self.producer = Producer({
            'bootstrap.servers': config,
            'message.max.bytes': 10485760,
            'message.timeout.ms': 60000
        })
        self.message_queue = []

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(err)

    def add_message(self, topic, key, value):
        self.message_queue.append((topic, key, value))

    def flush(self):
        for topic, key, value in self.message_queue:
            self.producer.produce(topic, key=key, value=value, callback=self.delivery_report)
        self.producer.flush()
        self.message_queue = []


producer = KafkaProducer(settings.KAFKA_BOOTSTRAP_SERVERS)
