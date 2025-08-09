import os
import json
import logging

from types import SimpleNamespace
from datetime import datetime, timedelta

from .fotmob_api import FotmobApi
from .fotmob_models import FotmobMatchData, FotmobGoal, FotmobPlayer, FotmobTeam, FotmobFixture

class FotmobService:
    """
    Provides services to interact with the Fotmob API.
    """

    def __init__(self):        
        self.api = FotmobApi()

    def get_teams(self, league_id):
        """
        Fetches team data from Fotmob API for a given league ID and returns a list of Team objects.
        """
        data = self.api.get_table(league_id)[0]["data"]

        data = json.loads(json.dumps(data), object_hook=lambda dictionary: SimpleNamespace(**dictionary))

        teams = []

        for team_data in data.table.all:
            team = FotmobTeam()
            team.stat_source_id = team_data.id
            team.name = team_data.name
            teams.append(team)

        return teams

    def get_players(self):
        """
        Fetches player data from Fotmob API and returns a list of players.
        """        
        teams = self.get_teams(47)

        players = []

        for team in teams:
            team_data = self.api.get_team(team.stat_source_id)

            if not team_data:
                continue

            team_data = json.loads(json.dumps(team_data), object_hook=lambda dictionary: SimpleNamespace(**dictionary))

            for member_data in team_data.squad.squad:
                if member_data.title != "coach":
                    for member in member_data.members:
                        player = {}
                        player["stat_source_id"] = member.id
                        player["name"] = member.name
                        players.append(player)

        return players
    
    def get_fixtures(self, league_id):
        """
        Fetches fixtures from Fotmob API for a given league ID.
        """
        league_json = self.api.get_league(league_id)
        league_data = json.loads(json.dumps(league_json), object_hook=lambda dictionary: SimpleNamespace(**dictionary))
        
        fixtures = []

        for fixture_data in league_data.matches.allMatches:
            fixture = FotmobFixture()
            fixture.stat_source_id = fixture_data.id
            fixture.round = fixture_data.round
            fixture.home_team_stat_source_id = fixture_data.home.id
            fixture.home_team_name = fixture_data.home.name
            fixture.away_team_stat_source_id = fixture_data.away.id
            fixture.away_team_name = fixture_data.away.name

            fixture_datetime = datetime.strptime(fixture_data.status.utcTime, "%Y-%m-%dT%H:%M:%SZ")
            fixture_datetime = fixture_datetime + timedelta(hours=2)
            fixture.datetime = fixture_datetime.strftime("%Y-%m-%d %H:%M:%S")
            fixtures.append(fixture)

        return fixtures

    def get_match(self, match_id):
        """
        Fetches match data from Fotmob API and returns a MatchData object.
        """
        data = self.api.get_match_details(match_id)

        data = json.loads(json.dumps(data), object_hook=lambda dictionary: SimpleNamespace(**dictionary))

        match_data = FotmobMatchData()

        # General match information ---------------------------------------------------------------

        general = data.general

        match_data.fotmob_id = general.matchId
        match_data.home_team_fotmob_id = general.homeTeam.id
        match_data.home_team_name = general.homeTeam.name
        match_data.away_team_fotmob_id = general.awayTeam.id
        match_data.away_team_name = general.awayTeam.name

        match_datetime = datetime.strptime(general.matchTimeUTC, "%a, %b %d, %Y, %H:%M %Z")
        match_datetime = match_datetime + timedelta(hours=2)
        match_data.datetime = match_datetime.strftime("%Y-%m-%d %H:%M")

        status = data.header.status

        if status.finished:
            match_data.elapsed = "FT"
            match_data.status = "FULL_TIME"
        elif status.started:
            match_data.elapsed = status.liveTime.short.replace("\u2019", "")
            match_data.status = "ACTIVE"
        else:
            match_data.elapsed = "N/A"
            match_data.status = "PENDING"
            return match_data

        # Event-based data (goals and cards) ------------------------------------------------------

        home_team_goals = 0
        away_team_goals = 0
        cards = {}

        events = data.content.matchFacts.events.events

        for event in events:
            if event.type == "Goal":
                goal = FotmobGoal()
                goal.player_fotmob_id = event.player.id
                goal.player_name = event.player.name
                goal.time = event.time

                if event.isHome:
                    goal.team_fotmob_id = match_data.home_team_fotmob_id
                    goal.team_name = match_data.home_team_name
                    home_team_goals += 1
                else:
                    goal.team_fotmob_id = match_data.away_team_fotmob_id
                    goal.team_name = match_data.away_team_name
                    away_team_goals += 1

                goal.penalty = event.goalDescriptionKey == "penalty"
                goal.own_goal = event.goalDescriptionKey == "owngoal"

                match_data.goals.append(goal)

            elif event.type == "Card":
                player_id = event.player.id
                if player_id not in cards:
                    cards[player_id] = {
                        "yellow_card_time": 0,
                        "red_card_time": 0   
                    }

                if event.card == "Yellow":
                    cards[player_id]["yellow_card_time"] = event.time
                elif event.card == "Red":
                    cards[player_id]["red_card_time"] = event.time

        # Player data -----------------------------------------------------------------------------

        lineup = data.content.lineup
        player_datas = []
        home_team_moms = {
            "rating": 0,
            "players": []
        }
        away_team_moms = {
            "rating": 0,
            "players": []
        }

        def add_player_data(player_list, team_fotmob_id, team_name, lineup_type, goals_conceded_count):
            for player_data in player_list:
                player_data.team_fotmob_id = team_fotmob_id
                player_data.team_name = team_name
                player_data.lineup = lineup_type
                player_data.goalsConceded = goals_conceded_count
                player_datas.append(player_data)

        add_player_data(lineup.homeTeam.starters, match_data.home_team_fotmob_id, match_data.home_team_name, "STARTING_LINEUP", away_team_goals)
        add_player_data(lineup.homeTeam.subs, match_data.home_team_fotmob_id, match_data.home_team_name, "SUBSTITUTE", away_team_goals)
        add_player_data(lineup.awayTeam.starters, match_data.away_team_fotmob_id, match_data.away_team_name, "STARTING_LINEUP", home_team_goals)
        add_player_data(lineup.awayTeam.subs, match_data.away_team_fotmob_id, match_data.away_team_name, "SUBSTITUTE", home_team_goals)

        for player_data in player_datas:
            player = FotmobPlayer()
            player.player_fotmob_id = player_data.id
            player.player_name = player_data.name
            player.team_fotmob_id = player_data.team_fotmob_id
            player.team_name = player_data.team_name
            player.lineup = player_data.lineup
            player.goals_conceded = player_data.goalsConceded

            if player.player_fotmob_id in cards:
                card_data = cards[player.player_fotmob_id]
                player.yellow_card_time = card_data.get("yellow_card_time")
                player.red_card_time = card_data.get("red_card_time")

            if hasattr(player_data, "performance"):
                performance = player_data.performance

                if hasattr(performance, "rating"):
                    player.rating = int(performance.rating * 100)

                if hasattr(performance, "events"):
                    for event in performance.events:
                        if event.type == "goal":
                            player.goals += 1
                        elif event.type == "assist":
                            player.goal_assists += 1
                        elif event.type == "ownGoal":
                            player.own_goals += 1

                if hasattr(performance, "substitutionEvents"):
                    for event in performance.substitutionEvents:
                        if event.type == "subIn":
                            player.substitution_on_time = event.time
                        elif event.type == "subOut":
                            player.substitution_off_time = event.time

                        # Fotmob doesn't provide a default rating for players who didn't play for long enough                            
                        if player.rating == 0:
                            player.rating = 600

                if player.team_fotmob_id == match_data.home_team_fotmob_id and player.rating >= home_team_moms["rating"]:
                    if player.rating > home_team_moms["rating"]:
                        home_team_moms["rating"] = player.rating
                        home_team_moms["players"] = [player]
                    else:
                        home_team_moms["players"].append(player)
                elif player.team_fotmob_id == match_data.away_team_fotmob_id and player.rating >= away_team_moms["rating"]  :
                    if player.rating > away_team_moms["rating"]:
                        away_team_moms["rating"] = player.rating
                        away_team_moms["players"] = [player]
                    else:
                        away_team_moms["players"].append(player)    

            match_data.players.append(player)

        def assign_man_of_the_match(players):
            if len(players) == 1:
                players[0].man_of_the_match = True
            elif len(players) > 1:
                for player in players:
                    player.shared_man_of_the_match = True

        assign_man_of_the_match(home_team_moms["players"])
        assign_man_of_the_match(away_team_moms["players"])

        return match_data

    def parse_fotmob_har(self, file_path):
        """
        Parses a .har file from Fotmob and updates the token in .fotmob_api_token.
        """
        if not os.path.exists(file_path):
            logging.debug("Fotmob HAR file not found at the specified path")
            return

        with open(file_path, "r") as file:
            har = json.loads(file.read(), object_hook=lambda dictionary: SimpleNamespace(**dictionary))
            token = None
            for entry in har.log.entries:
                if 'matchDetails' in entry.request.url:
                    for header in entry.request.headers:
                        if header.name == 'x-mas':
                            token = header.value

            if not token:
                logging.error(f"Fotmob token not found in {file_path}")
            else:
                with open('.fotmob_api_token', 'w') as token_file:
                    token_file.write(token)
                    logging.info(f"Fotmob token updated in .fotmob_api_token: {token}")

            os.remove(file_path)
