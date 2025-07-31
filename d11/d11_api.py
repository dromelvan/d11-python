import os
import requests
import logging

class D11Api:
    """
    Provides methods to interact with the D11 API.
    """

    def get_teams(self):
        """
        Gets all teams.
        """
        url = os.getenv("D11_API_BASE_URL") + os.getenv("D11_API_TEAMS_ENDPOINT")
        return self._call_api(url)

    def get_match(self, match_id):
        """
        Gets match data for a given match ID.
        """
        url_template = os.getenv("D11_API_BASE_URL") + os.getenv("D11_API_MATCH_ENDPOINT")
        url = url_template.format(match_id=match_id)
        return self._call_api(url)

    def _call_api(self, url):
        """        
        Makes a GET request to the D11 API and returns the JSON response.
        If an error occurs, it logs the error and returns None.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching D11 data from {url}: {e}")
            return None
