from .d11_schedule import D11Schedule
from .d11_mq_listener import D11MqListener

class D11Daemon:
    """
    Runs the D11 scheduler and MQ listener.
    """
    def __init__(self):
        self.d11_mq_listener = D11MqListener()
        self.d11_schedule = D11Schedule()        

    def start(self):
        """
        Starts the D11 scheduler and MQ listener.
        """
        self.d11_mq_listener.start()
        self.d11_schedule.start()

        # Scheduler will block. We'll get here when it is interrupted
        self.d11_mq_listener.stop()
