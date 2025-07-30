import os
import logging
import stomp


class ArtemisListener(stomp.ConnectionListener):
    """
    Listens to messages from ArtemisMQ.
    """
    active_match_queue = os.getenv('D11_MQ_ACTIVE_MATCH_QUEUE', 'D11::ACTIVE_MATCH')
    ping_queue = os.getenv('D11_PING_QUEUE', 'D11::PING')

    def __init__(self, artemis_connection_manager, queues, on_active_match):
        self.queues = queues
        self.on_active_match = on_active_match
        self.artemis_connection_manager = artemis_connection_manager

    def on_error(self, frame):
        """
        Handles MQ errors.
        """
        logging.error('Artemis MQ error: %s %s', frame.headers.get('message', ''), frame.body)

    def on_disconnected(self):
        """
        Handles disconnection by reconnecting to Artemis MQ. This should't happen since the connection
        has a heartbeat but it happens now and then anyway for some unknown reason.
        """
        logging.warning('Disconnected from Artemis MQ -- reconnecting...')
        self.artemis_connection_manager.reconnect()

    def on_message(self, frame):
        """
        Handles a message by checking destination and forwarding it to the relevant method.
        """
        destination = frame.headers.get('destination', '')

        if destination == self.active_match_queue:
            self.on_active_match(frame)
        elif destination == self.ping_queue:
            self.on_ping(frame)

    def on_ping(self, frame):
        """
        Handles a ping message.
        """
        logging.info('Ping received: %s', frame.body)
