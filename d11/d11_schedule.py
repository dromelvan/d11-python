import os
import time
import logging
import schedule

from d11 import D11Service

class D11Schedule:
    """
    Schedules periodic tasks.
    """
    def __init__(self):
        self.d11_service = D11Service()

    def task_update_squads(self):
        """
        Triggers a squad update.
        """
        competition_id = os.getenv('PREMIER_LEAGUE_DEFAULT_COMPETITION_ID')
        season = os.getenv('PREMIER_LEAGUE_DEFAULT_SEASON')

        if competition_id is None or season is None:
            logging.error("Competition id or season is not defined in .env")

        self.d11_service.update_squads(competition_id, season)

    def start(self):
        """
        Starts the scheduler.
        """
        schedule.every().day.at("10:00").do(self.task_update_squads)

        logging.info("D11 schedule started...")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("D11 schedule stopped")
