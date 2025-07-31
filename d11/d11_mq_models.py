import json

class UpdateSquadMessage:
    """
    Message that contains data for updating a team squad.
    """
    def __init__(self):
        self.team_data = None

    def to_dict(self):
        return {
            "teamData": self.team_data.to_dict() if self.team_data else None
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class UpdateMatchMessage:
    """
    Message that contains data for upodating a match.
    """
    def __init__(self):
        self.match_data = None
        self.finish = None

    def to_dict(self):
        return {
            "matchData": self.match_data,
            "finish": self.finish
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
