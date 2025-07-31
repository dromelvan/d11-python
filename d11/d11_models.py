import json

class ActiveMatch:
    """
    Active match ID and finish propery.
    """
    def __init__(self):
        self.match_id = None
        self.finish = False

    def to_dict(self):
        return {
            "matchId": self.match_id,
            "finish": self.finish
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


class TeamSquadData:
    """
    Squad data for a Premier League team.
    """
    def __init__(self):
        self.id = None
        self.name = None
        self.players = []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "players": [player.to_dict() for player in self.players]
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    
class TeamSquadPlayerData:
    """
    Data for a player in a Premier League team squad.
    """
    def __init__(self):
        self.id = None
        self.name = None
        self.shirtNumber = None
        self.position = None
        self.nationality = None
        self.photoId = None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "shirtNumber": self.shirtNumber,
            "position": self.position,
            "nationality": self.nationality,
            "photoId": self.photoId
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
