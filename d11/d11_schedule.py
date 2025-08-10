import os
import time
import logging
import schedule
import random

from datetime import datetime, timedelta

from d11 import D11Service
from fotmob import FotmobService

UPDATE_FOTMOB_TOKEN_TAG = "update_fotmob_token"

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

        fotmob_service = FotmobService()
        fotmob_service.get_fotmob_api_token()

        # After running, schedule the next run with jitter
        next_run = datetime.now() + timedelta(hours=2) + timedelta(minutes=random.randint(-5, 5))
        if next_run.hour < 9:
            next_run = next_run.replace(hour=9, minute=random.randint(0, 30))
        elif next_run.hour >= 24:
            # Push to next day's 9:00
            next_run = (next_run + timedelta(days=1)).replace(hour=9, minute=random.randint(0, 59))

        schedule.clear(UPDATE_FOTMOB_TOKEN_TAG)
        schedule.every().day.at(next_run.strftime("%H:%M")).do(self.task_update_fotmob_token).tag(UPDATE_FOTMOB_TOKEN_TAG)
        logging.info(f"Next run scheduled for {next_run.strftime('%Y-%m-%d %H:%M')}")

    def start(self):
        """
        Starts the scheduler.
        """
        schedule.every().day.at("10:00").do(self.task_update_squads)
        schedule.every().minute.do(self.task_update_fotmob_token).tag(UPDATE_FOTMOB_TOKEN_TAG)


        logging.info("D11 schedule started...")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("D11 schedule stopped")
