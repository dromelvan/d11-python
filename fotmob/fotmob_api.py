import os
import time
import requests
import logging

from .fotmob_token_manager import FotmobTokenManager

SESSION_REFRESH_INTERVAL = 3 * 60 * 60
FOTMOB_API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:146.0) "
        "Gecko/20100101 Firefox/146.0"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
}

class FotmobApi:
    """
    Provides methods to interact with the Fotmob API.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(FOTMOB_API_HEADERS)

        self.last_refresh = 0
        self._refresh_session()

        self.fotmob_token_manager = FotmobTokenManager()

    def _deprecated_get_headers(self, url):
        """
        Returns the headers required for Fotmob API requests, including the authentication token.
        THIS USAGE IS DEPRECATED: Fotmob changed their authentication mechanism.
        """
        token = self.fotmob_token_manager.get_token(url)

        if not token:
            logging.error("Authentication token is not available.")
            return {}
        return {
            "x-mas": token
        }
        
    def get_table(self, league_id):
        """
        Gets the league table for a given league ID.
        """
        url_template = os.getenv("FOTMOB_API_BASE_URL") + os.getenv("FOTMOB_API_TABLE_ENDPOINT")
        url = url_template.format(league_id=league_id)
        return self._call_api(url)
    
    def get_league(self, league_id):
        """
        Gets the league information for a given league ID.
        """
        url_template = os.getenv("FOTMOB_API_BASE_URL") + os.getenv("FOTMOB_API_LEAGUE_ENDPOINT")
        url = url_template.format(league_id=league_id)
        return self._call_api(url)

    def get_team(self, team_id):
        """
        Gets team information for a given team ID.
        """
        url_template = os.getenv("FOTMOB_API_BASE_URL") + os.getenv("FOTMOB_API_TEAM_ENDPOINT")
        url = url_template.format(team_id=team_id)
        return self._call_api(url)

    def get_match_details(self, match_id):
        """
        Gets detailed match information for a given match ID.
        """
        url_template = os.getenv("FOTMOB_API_BASE_URL") + os.getenv("FOTMOB_API_MATCH_DETAILS_ENDPOINT")
        url = url_template.format(match_id=match_id)
        return self._call_api(url)

    def _call_api(self, url):
        """        
        Makes a GET request to the Fotmob API and returns the JSON response.
        If an error occurs, it logs the error and returns None.
        """
        try:
            if time.time() - self.last_refresh > SESSION_REFRESH_INTERVAL:
                self._refresh_session()

            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching Fotmob data from {url}: {e}")
            return None

    def _refresh_session(self):
        """
        Calls Footmob homepage to refresh session cookies.
        """
        try:
            resp = self.session.get("https://www.fotmob.com/", timeout=15)
            resp.raise_for_status()
            self.last_refresh = time.time()
            logging.info("Fotmob session refreshed.")
        except Exception as e:
            logging.error(f"Error refreshing Fotmob session: {e}")
