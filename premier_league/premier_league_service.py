import json

from types import SimpleNamespace

from .premier_league_api import PremierLeagueApi
from .premier_league_models import PremierLeagueTeam, PremierLeaguePlayer, PremierLeaguePlayerCountry, PremierLeaguePlayerName, PremierLeaguePlayerDates

class PremierLeagueService:
    """
    Provides services to interact with the Premier League API.
    """

    def __init__(self):        
        self.api = PremierLeagueApi()

    def get_teams(self, competition_id, season):
        """
        Fetches team data from Premier League API for a given competition ID and returns a list of Team objects.
        """
        data = self.api.get_clubs(competition_id=competition_id, season=season)["data"]

        data = json.loads(json.dumps(data), object_hook=lambda dictionary: SimpleNamespace(**dictionary))

        teams = []

        for team_data in data:
            team = PremierLeagueTeam()
            team.stat_source_id = team_data.id
            team.name = team_data.name
            teams.append(team)

        return teams
    
    def get_players(self, competition_id, season, team_id):
        """
        Fetches player data from Premier League API for a given competition ID, season, and team ID.
        """
        data = self.api.get_squad(competition_id=competition_id, season=season, team_id=team_id)["players"]

        data = json.loads(json.dumps(data), object_hook=lambda dictionary: SimpleNamespace(**dictionary))

        players = []

        for player_data in data:
            player = PremierLeaguePlayer()
            player.country = PremierLeaguePlayerCountry(
                iso_code=player_data.country.isoCode,
                country=player_data.country.country,
                demonym=player_data.country.demonym
            )
            player.loan = player_data.loan
            player.country_of_birth = getattr(player_data, 'countryOfBirth', None)
            player.name = PremierLeaguePlayerName(
                last=player_data.name.last,
                display=player_data.name.display,
                first=player_data.name.first
            )
            player.shirt_num = getattr(player_data, 'shirtNum', None)
            player.weight = getattr(player_data, 'weight', None)

            player.dates = PremierLeaguePlayerDates(
                joined_club=player_data.dates.joinedClub,
                birth=player_data.dates.birth
            )
            player.id = player_data.id
            player.position = player_data.position
            player.preferred_foot = getattr(player_data, 'preferredFoot', None)

            players.append(player)

        return players


