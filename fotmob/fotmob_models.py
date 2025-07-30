import json

class FotmobGoal:
    """
    Represents a goal event in a Fotmob match, including player and team info, time, and whether it was a penalty or own goal.
    """    
    def __init__(self):
        self.player_fotmob_id = None
        self.player_name = None
        self.team_fotmob_id = None
        self.team_name = None
        self.time = None
        self.penalty = None
        self.own_goal = None

    def to_dict(self):
        return {
            "playerWhoscoredId": self.player_fotmob_id,
            "playerName": self.player_name,
            "teamWhoscoredId": self.team_fotmob_id,
            "teamName": self.team_name,
            "time": self.time,
            "penalty": self.penalty,
            "ownGoal": self.own_goal
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


class FotmobPlayer:
    """
    Represents a player in a Fotmob match, including stats, team, and event info.
    """    
    def __init__(self):
        self.player_id = None
        self.player_fotmob_id = None
        self.player_name = None
        self.country_id = 1
        self.position_id = 0
        self.team_fotmob_id = None
        self.team_name = None
        self.lineup = None
        self.substitution_on_time = 0
        self.substitution_off_time = 0
        self.goals = 0
        self.goal_assists = 0
        self.own_goals = 0
        self.goals_conceded = 0
        self.yellow_card_time = 0
        self.red_card_time = 0
        self.man_of_the_match = False
        self.shared_man_of_the_match = False
        self.rating = 0
        self.played_position = ''
        self.height = 0

    def to_dict(self):
        return {
            "playerId": self.player_id,
            "playerWhoscoredId": self.player_fotmob_id,
            "playerName": self.player_name,
            "countryId": self.country_id,
            "positionId": self.position_id,
            "teamWhoscoredId": self.team_fotmob_id,
            "teamName": self.team_name,
            "lineup": self.lineup,
            "substitutionOnTime": self.substitution_on_time,
            "substitutionOffTime": self.substitution_off_time,
            "goals": self.goals,
            "goalAssists": self.goal_assists,
            "ownGoals": self.own_goals,
            "goalsConceded": self.goals_conceded,
            "yellowCardTime": self.yellow_card_time,
            "redCardTime": self.red_card_time,
            "manOfTheMatch": self.man_of_the_match,
            "sharedManOfTheMatch": self.shared_man_of_the_match,
            "rating": self.rating,
            "playedPosition": self.played_position,
            "height": self.height
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class FotmobTeam:
    """
    Represents a team in a Fotmob match, including IDs, names, and match round info.
    """    
    def __init__(self):
        self.stat_source_id = None
        self.round = None
        self.home_team_stat_source_id = None
        self.home_team_name = None
        self.away_team_stat_source_id = None
        self.away_team_name = None
        self.datetime = None

    def to_dict(self):
        return {
            "statSourceId": self.stat_source_id,
            "round": self.round,
            "home_team_stat_source_id": self.home_team_stat_source_id,
            "home_team_name": self.home_team_name,
            "away_team_stat_source_id": self.away_team_stat_source_id,
            "away_team_name": self.away_team_name,
            "datetime": self.datetime
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class FotmobFixture:
    """
    Represents a fixture (scheduled match) in Fotmob.
    """    
    def __init__(self):
        self.stat_source_id = None

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class FotmobMatchData:
    """
    Represents all relevant data for a Fotmob match, including teams, goals, players, and status.
    """    
    def __init__(self):
        self.match_id = None
        self.fotmob_id = None
        self.home_team_fotmob_id = None
        self.home_team_name = None
        self.away_team_fotmob_id = None
        self.away_team_name = None
        self.datetime = None
        self.elapsed = None
        self.status = None
        self.goals = []
        self.players = []

    def to_dict(self):
        return {
            "matchId": self.match_id,
            "whoscoredId": self.fotmob_id,
            "homeTeamWhoscoredId": self.home_team_fotmob_id,
            "homeTeamName": self.home_team_name,
            "awayTeamWhoscoredId": self.away_team_fotmob_id,
            "awayTeamName": self.away_team_name,
            "datetime": self.datetime,
            "elapsed": self.elapsed,
            "status": self.status,
            "goals": [g.to_dict() for g in self.goals],
            "players": [p.to_dict() for p in self.players]
        }

    def to_json(self, ensure_ascii=True):
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=2)
