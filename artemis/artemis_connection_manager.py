import os
import stomp
import logging


class ArtemisConnectionManager:
    """
    Manages singleton connection to Artemis MQ.    
    """

    def __init__(self):
        self.connection = None
        self.host = os.getenv('D11_MQ_HOST', 'localhost')
        self.port = os.getenv('D11_MQ_PORT', 61616)
        self.user = os.getenv('D11_MQ_USER', 'user')
        self.password = os.getenv('D11_MQ_PASSWORD', 'password')
        self.listener = None

    def connect(self):
        """
        Connects to Artemis MQ, if not already connected.
        """
        if self.connection is None or not self.connection.is_connected():
            self.connection = stomp.Connection([(self.host, self.port)], heartbeats=(30000, 30000))
            self.connection.connect(login=self.user, passcode=self.password, wait=True)
            logging.info('Connected to Artemis MQ on %s:%s', self.host, self.port)

    def disconnect(self):
        """
        Disconnects from Artemis MQ.
        """
        if self.connection and self.connection.is_connected():
            self.connection.disconnect()
            self.connection = None
            logging.info('Disconnected from Artemis MQ')
    
    def reconnect(self):
        """
        Reconnects to Artemis MQ and resets the listener, if there is one.
        """
        self.disconnect()
        self.connect()
        self.set_listener(self.listener)

    def get_connection(self):
        """
        Gets a singleton Artemis MQ connection.
        """
        self.connect()
        return self.connection

    def set_listener(self, listener):
        """
        Sets a listener and subscribes to all queues the listener wants to listen to.
        """
        self.connect()
        self.listener = listener
        if self.connection and self.connection.is_connected():
            listener_name = listener.__class__.__name__
            self.connection.set_listener(listener_name, listener)
            logging.info('Listener %s set for Artemis MQ', listener_name)

            for queue in self.listener.queues:
                self.connection.subscribe(destination=queue, id=queue, ack='auto')
                logging.info('Subscribed to queue: %s', queue)
