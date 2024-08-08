import os


from   config.logger       import log

from confluent_kafka.admin import AdminClient, NewTopic, KafkaException, KafkaError


kadmin_client = AdminClient({ "bootstrap.servers": "kafka" })


def create_kafka_topics():
    new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1) for topic in [os.environ["KAFKA_TOPIC"]]]

    fs = kadmin_client.create_topics(new_topics)

    for topic, f in fs.items():
        try:
            f.result()
            log.info(f"kadmin_client - Topic <{topic}> created")
        except KafkaException as e:
            if e.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                log.info(f"kadmin_client - Topic <{topic}> already exists; proceeding...")
            else:
                print(f"kadmin_client - error @ <{topic}>: {e}")

