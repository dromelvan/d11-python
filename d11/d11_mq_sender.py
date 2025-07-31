from artemis import artemis_sender
from .d11_mq_models import UpdateMatchMessage
import os

class D11MqSender:
    """
    Sends D11 messages to whatever MQ is being used.
    """
    def __init__(self):
        self.artemis_sender = artemis_sender

    def send_ping(self):
        """
        Sends a ping message. Only used for testing.
        """
        destination = os.getenv('D11_MQ_PING_QUEUE', 'D11::PING')
        self.artemis_sender.send_message(destination=destination, body='{ "ping": true }')

    def send_update_squad_message(self, update_squad_message):
        """
        Sends a message containing data for updating a team squad.
        """
        destination = os.getenv('D11_MQ_UPDATE_SQUAD_QUEUE', 'D11::UPDATE_SQUAD')
        self.artemis_sender.send_message(destination=destination, body=update_squad_message.to_json())

    def send_update_match_message(self, match_data, finish):
        """
        Sends a message containing data for upodating a match.
        """
        destination = os.getenv('D11_MQ_MATCH_DATA_QUEUE', 'D11::UPDATE_MATCH')

        update_match_message = UpdateMatchMessage()
        update_match_message.match_data = match_data
        update_match_message.finish = finish
        
        self.artemis_sender.send_message(destination=destination, body=update_match_message.to_json())

d11_mq_sender = D11MqSender()
