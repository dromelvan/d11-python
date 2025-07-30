import os
import requests
import logging

class FotmobApi:
    """
    Provides methods to interact with the Fotmob API.
    """

    authentocation_token = None

    def get_authentication_token(self):
        """
        Gets an authentication token for the Fotmob API. The url for this is a bit sketchy but it works for now.
        """
        if not self.authentocation_token:
            try:
                response = requests.get(os.getenv("FOTMOB_AUTHENTICATION_TOKEN_URL"))
                response.raise_for_status()
                token = response.json().get("x-mas")
                if not token:
                    raise ValueError("No 'x-mas' field in response")
                self.authentocation_token = token
            except Exception as e:
                logging.error(f"Error getting authentication token: {e}")
        return self.authentocation_token

    def get_headers(self):
        """
        Returns the headers required for Fotmob API requests, including the authentication token.
        """
        token = self.get_authentication_token()
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
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching Fotmob data from {url}: {e}")
            return None