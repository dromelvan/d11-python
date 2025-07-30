import json

class PremierLeagueTeam:
    """
    Represents a Premier League team.
    """    
    def __init__(self):
        self.stat_source_id = None
        self.name = None

    def to_dict(self):
        return {
            "statSourceId": self.stat_source_id,
            "name": self.name
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class PremierLeaguePlayer:
    """
    Represents a Premier League player.
    """
    def __init__(self):
        self.country = None  # PremierLeaguePlayerCountry
        self.loan = None
        self.country_of_birth = None
        self.name = None  # PremierLeaguePlayerName
        self.shirt_num = None
        self.weight = None
        self.dates = None  # PremierLeaguePlayerDates
        self.id = None
        self.position = None
        self.preferred_foot = None

    def to_dict(self):
        return {
            "country": self.country.to_dict() if self.country else None,
            "loan": self.loan,
            "countryOfBirth": self.country_of_birth,
            "name": self.name.to_dict() if self.name else None,
            "shirtNum": self.shirt_num,
            "weight": self.weight,
            "dates": self.dates.to_dict() if self.dates else None,
            "id": self.id,
            "position": self.position,
            "preferredFoot": self.preferred_foot
        }

    def to_json(self, ensure_ascii=True):
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=2)

class PremierLeaguePlayerCountry:
    """
    Represents a Premier League player country.
    """    
    def __init__(self, iso_code, country, demonym):
        self.iso_code = iso_code
        self.country = country
        self.demonym = demonym

    def to_dict(self):
        return {
            "isoCode": self.iso_code,
            "country": self.country,
            "demonym": self.demonym
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class PremierLeaguePlayerName:
    """
    Represents a Premier League player name.
    """
    def __init__(self, last, display, first):
        self.last = last
        self.display = display
        self.first = first

    def to_dict(self):
        return {
            "last": self.last,
            "display": self.display,
            "first": self.first
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2) 

class PremierLeaguePlayerDates:
    """
    Represents a set of dates relevant to a Premier League player.
    """
    def __init__(self, joined_club, birth):
        self.joined_club = joined_club
        self.birth = birth

    def to_dict(self):
        return {
            "joinedClub": self.joined_club,
            "birth": self.birth
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)
