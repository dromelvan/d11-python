# premier_league/__init__.py
from .premier_league_api import PremierLeagueApi
from .premier_league_service import PremierLeagueService
from .premier_league_models import PremierLeagueTeam, PremierLeaguePlayer, PremierLeaguePlayerCountry, PremierLeaguePlayerName, PremierLeaguePlayerDates

premier_league_service = PremierLeagueService()

__all__ = ["premier_league_service", "PremierLeagueApi", "PremierLeagueService", "PremierLeagueTeam", "PremierLeaguePlayer", "PremierLeaguePlayerCountry", "PremierLeaguePlayerName", "PremierLeaguePlayerDates"]
