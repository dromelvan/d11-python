import logging


class ArtemisSender:
    """
    Sends messages to Artemis MQ.
    """

    def __init__(self, artemis_connection_manager):
        self.artemis_connection_manager = artemis_connection_manager

    def send_message(self, destination, body):
        """
        Sends a message to a specific destination on Artemis MQ.
        """
        connection = self.artemis_connection_manager.get_connection()
        connection.send(destination=destination, body=body, headers={'content-type': 'application/json'})
        logging.debug('Message sent to destination: %s', destination)
