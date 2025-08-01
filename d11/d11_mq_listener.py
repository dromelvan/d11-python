import os
import json
import logging
from types import SimpleNamespace

from artemis import artemis_connection_manager, ArtemisListener

from .d11_service import D11Service

active_match_queue = os.getenv('D11_MQ_ACTIVE_MATCH_QUEUE', 'D11::ACTIVE_MATCH')
ping_queue = os.getenv('D11_PING_QUEUE', 'D11::DOWNLOAD_WHOSCORED_MATCH')

class D11MqListener:
    """
    Implements handling of D11 messages on MQ queues.
    """
    def __init__(self):
        self.d11_service = D11Service()
        self.artemis_connection_manager = artemis_connection_manager

    def start(self):
        """
        Starts the MQ listener.
        """
        artemis_listener = ArtemisListener(artemis_connection_manager=self.artemis_connection_manager, queues=[active_match_queue, ping_queue], on_active_match=self.on_active_match)
        self.artemis_connection_manager.set_listener(artemis_listener)

    def stop(self):
        """
        Disconnects from the MQ.
        """
        self.artemis_connection_manager.disconnect()

    def on_active_match(self, frame):        
        """
        Handles an active match messages by triggering a match update.
        """
        active_match = json.loads(frame.body, object_hook=lambda d: SimpleNamespace(**d))
        logging.info('on_active_match: match_id %s, finish: %s', active_match.matchId, active_match.finish)
        self.d11_service.update_match(active_match.matchId, active_match.finish)
