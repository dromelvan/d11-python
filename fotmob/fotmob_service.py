import os
from pathlib import Path
import re
import json
import logging
import time
import unicodedata

from types import SimpleNamespace
from datetime import datetime, timedelta

from .fotmob_api import FotmobApi
from .fotmob_cookie_manager import FotmobCookieManager
from .fotmob_selenium import FotmobSelenium
from .fotmob_models import FotmobMatchData, FotmobGoal, FotmobPlayer, FotmobTeam, FotmobFixture

class FotmobService:
    """
    Provides services to interact with the Fotmob API.
    """

    def __init__(self):        
        self.api = FotmobApi()
        self.selenium = FotmobSelenium()

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

    def get_players(self, league_id):
        """
        Fetches player data from Fotmob API and returns a list of players.
        """        
        teams = self.get_teams(league_id)

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

            # Replace "Z" with "+00:00" so fromisoformat understands it and convert to local time zone
            fixture_datetime = datetime.fromisoformat(fixture_data.status.utcTime.replace("Z", "+00:00")).astimezone()

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
                else:
                    cards[player_id]["red_card_time"] = event.time

        # Fetch more precise ratings --------------------------------------------------------------                    

        player_ratings = {}

        for player_id, player in vars(data.content.playerStats).items():
            try:
                # Ensure player.stats exists and is iterable
                if not getattr(player, "stats", None):
                    continue

                # Find the "top_stats" section
                top_stats_section = next(
                    (s for s in player.stats if getattr(s, "key", None) == "top_stats"),
                    None
                )
                if not top_stats_section:
                    continue

                # Ensure the stats map exists
                stats_map = vars(getattr(top_stats_section, "stats", SimpleNamespace()))
                if "FotMob rating" not in stats_map:
                    continue

                # Extract the value safely
                rating_value = getattr(stats_map["FotMob rating"].stat, "value", None)
                if rating_value is not None:
                    player_ratings[int(player_id)] = rating_value

            except Exception:
                # Skip player if any unexpected structure is found
                continue

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
            player.played_position = "N/A"

            if player.player_fotmob_id in player_ratings:
                player.rating = int(player_ratings[player.player_fotmob_id] * 100)
            elif player.lineup == "STARTING_LINEUP":
                player.rating = 600  # Default rating for starting players since Fotmob takes a few minutes to give a rating

            if player.player_fotmob_id in cards:
                card_data = cards[player.player_fotmob_id]
                player.yellow_card_time = card_data.get("yellow_card_time")
                player.red_card_time = card_data.get("red_card_time")

            if hasattr(player_data, "performance"):
                performance = player_data.performance

                # We're not using this rating for now since it only has once decimal
                # if hasattr(performance, "rating"):
                #     player.rating = int(performance.rating * 100)

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
                        if not player.rating or player.rating == 0:
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

    def get_fotmob_api_token(self):
        """
        Fetches the Fotmob API token using Selenium and writes it to .fotmob_api_token.
        """
        token = self.selenium.get_api_token()
        if not token:
            logging.error("Failed to retrieve Fotmob API token using Selenium")
        else:
            with open('.fotmob_api_token', 'w') as token_file:
                token_file.write(token)
                logging.info(f"Fotmob API token via Selenium updated in .fotmob_api_token: {token}")    

    def get_fotmob_turnstile_cookie(self):
        """
        Fetches the Fotmob turnstile cookie from Firefox profiles and logs it.
        """
        cookie_manager = FotmobCookieManager()
        cookie = cookie_manager.find_latest_turnstile_cookie()

        if not cookie:
            logging.error("Fotmob turnstile cookie not found in any Firefox profile")
        else:
            logging.info(f"Fotmob turnstile cookie found: {cookie}")
            expiry_raw = cookie.get("expiry", 0)
            expiry = self.normalize_unix_time(expiry_raw)

            if expiry == 0:
                logging.info("Expires at: Session cookie")
            else:
                logging.info(
                    "Expires at: %s",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expiry)),
                )

            cookies_file = Path(".fotmob_cookies")

            try:
                with cookies_file.open("w") as f:
                    json.dump(
                        {cookie["name"]: cookie["value"]},
                        f,
                        indent=2,
                    )
            except Exception as e:
                logging.error(f"Failed to write Fotmob cookies file: {e}")
                return None            

    def normalize_unix_time(self, ts: int) -> int:
        """
        Convert Firefox cookie time to seconds if needed.
        Handles seconds, milliseconds, or microseconds.
        """
        if ts == 0:
            return 0

        # microseconds
        if ts > 10_000_000_000_000:
            return ts // 1_000_000

        # milliseconds
        if ts > 10_000_000_000:
            return ts // 1_000

        # already seconds
        return ts

    def generate_pl_fixtures(self, league_id):
        """
        Generates Premier League fixture migration for the upcoming season.
        """
        fixtures = FotmobService().get_fixtures(league_id)

        sql = """insert into ${schema}.match (home_team_id, away_team_id, match_week_id, stadium_id, whoscored_id, datetime, home_team_goals, away_team_goals, previous_home_team_goals, previous_away_team_goals, elapsed, status, created_at, updated_at)
        values ((select (id) from ${schema}.team where whoscored_id = {home_team_id}), (select (id) from ${schema}.team where whoscored_id = {away_team_id}),
                (select (id) from ${schema}.match_week where match_week_number = {match_week_number} and season_id = (select max(id) from ${schema}.season)),
                (select (stadium_id) from ${schema}.team where id = (select (id) from ${schema}..team where whoscored_id = {home_team_id})),
                {stat_source_id}, '{datetime}', 0, 0, 0, 0, 'N/A', 0, now()::timestamp, now()::timestamp);"""
        migration = [];

        for fixture in fixtures:
            home_team_id = fixture.home_team_stat_source_id
            away_team_id = fixture.away_team_stat_source_id

            fixture_sql = sql.format(sql, schema='{flyway:defaultSchema}', home_team_id=home_team_id, away_team_id=away_team_id, match_week_number=fixture.round, stat_source_id=fixture.stat_source_id, datetime=fixture.datetime)
            migration.append(fixture_sql)

        with open('pl_fixtures.sql', 'w') as f:
            for line in migration:
                f.write(f"{line}\n")

    def generate_missing_player_ids(self, league_id, id_file_name):
        """
        Gets players from all teams in Fotmob and generates sql for updating fotmob id for ids that are not found in the provided file.
        """
        players = self.get_players(league_id)

        ids = []
        with open(id_file_name, 'r') as f:
            for id in f:            
                id = id.strip()
                ids.append(int(id))

        def parameterize_name(name):
            name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
            name = name.lower()
            name = re.sub(r'[^a-z0-9]+', '-', name)
            name = name.strip('-')
            return name

        sql = [];
        for player in players:
            if player['stat_source_id'] not in ids:
                sql.append(f"update production.player set whoscored_id = {player['stat_source_id']} where parameterized_name = '{parameterize_name(player['name'])}';")

        with open('update_player_ids.sql', 'w') as f:
            for line in sql:
                f.write(f"{line}\n")
