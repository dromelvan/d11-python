import os
import time
import logging
import schedule

from d11 import D11Service
from fotmob import FotmobService

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

    def task_update_fotmob_token(self):
        """
        Triggers a Fotmob token update.
        """
        file_path = os.getenv('FOTMOB_HAR_FILE_PATH')
        if file_path is None:
            logging.error("FOTMOB_HAR_FILE_PATH is not defined in .env")
            return

        fotmob_service = FotmobService()
        fotmob_service.parse_fotmob_har(file_path)  

    def start(self):
        """
        Starts the scheduler.
        """
        schedule.every().day.at("10:00").do(self.task_update_squads)
        schedule.every().minute.do(self.task_update_fotmob_token)

        logging.info("D11 schedule started...")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("D11 schedule stopped")
