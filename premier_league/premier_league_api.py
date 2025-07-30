import os
import requests
import logging

class PremierLeagueApi:
    """
    Provides methods to interact with the Premier League API.
    """

    def get_clubs(self, competition_id, season):
        """
        Gets the participating clubs for a given competition ID.
        """
        url_template = os.getenv("PREMIER_LEAGUE_API_V1_BASE_URL") + os.getenv("PREMIER_LEAGUE_CLUBS_ENDPOINT")
        url = url_template.format(competition_id=competition_id, season=season)
        return self._call_api(url)

    def get_squad(self, competition_id, season, team_id):
        """
        Gets the squad for a given team ID in a specific competition and season.
        """
        url_template = os.getenv("PREMIER_LEAGUE_API_V2_BASE_URL") + os.getenv("PREMIER_LEAGUE_SQUAD_ENDPOINT")
        url = url_template.format(competition_id=competition_id, season=season, team_id=team_id)
        return self._call_api(url)

    def _call_api(self, url):
        """        
        Makes a GET request to the Premier League API and returns the JSON response.
        If an error occurs, it logs the error and returns None.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching Premier League data from {url}: {e}")
            return None

