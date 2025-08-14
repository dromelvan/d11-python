import os
import json
import shutil
import hashlib
import logging

from types import SimpleNamespace
from fotmob import FotmobService
from premier_league import PremierLeagueService

from .d11_api import D11Api
from .d11_models import TeamSquadData, TeamSquadPlayerData
from .d11_mq_models import UpdateSquadMessage
from .d11_mq_sender import D11MqSender

squad_data_directory = os.getenv('PREMIER_LEAGUE_SQUAD_DIRECTORY', 'data')
match_data_directory = os.getenv('FOTMOB_DATA_DIRECTORY', 'data')

class D11Service:
    """
    Provides services to interact with the Fotmob API.
    """

    def __init__(self):        
        self.api = D11Api()
        self.d11_mq_sender = D11MqSender()

        self.fotmob_service = FotmobService()
        self.premier_league_service = PremierLeagueService()        

    def get_team_id_map(self):
        """
        Gets mappings of stat source IDs to D11 IDs for Premier League teams.
        """
        teams_json = self.api.get_teams();

        teams = json.loads(json.dumps(teams_json), object_hook=lambda dictionary: SimpleNamespace(**dictionary))
        team_id_map = {}

        for team in teams:
            team_id_map[team.whoscoredId] = team.id

        return team_id_map

    def update_squads(self, competition_id, season):
        """
        Downloads squad data from the Premier League API for a competition and season and sends update squad data messages to the D11 MQ.
        """
        teams = self.premier_league_service.get_teams(competition_id, season)

        for team in teams:
            logging.info(f"Updating team squad for {team.name} ({team.stat_source_id})")

            team_squad_data = TeamSquadData()
            team_squad_data.id = team.stat_source_id
            team_squad_data.name = team.name
            team_squad_data.players = []

            players = self.premier_league_service.get_players(competition_id, season, team.stat_source_id)
            for player in players:
                team_squad_player_data = TeamSquadPlayerData()
                team_squad_player_data.id = player.id
                team_squad_player_data.name = player.name.display if player.name else None
                team_squad_player_data.shirtNumber = player.shirt_num
                team_squad_player_data.position = player.position
                team_squad_player_data.nationality = player.country.country if player.country else None
                team_squad_player_data.photoId = player.id

                team_squad_data.players.append(team_squad_player_data)
            
            update_squad_message = UpdateSquadMessage()
            update_squad_message.team_data = team_squad_data

            directory = squad_data_directory.format(
                season=season
            )

            file_name = f"{team.name}.json"

            full_path = os.path.join(directory, file_name)

            os.makedirs(directory, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(update_squad_message.to_dict(), f, ensure_ascii=False, indent=2)

            self.d11_mq_sender.send_update_squad_message(update_squad_message)
            logging.info(f"Team squad data for {team.name} sent to MQ")


    def update_match(self, match_id, finish):
        """
        Downloads match data from the stat source, saves the json to a file and sends an update match message to the D11 MQ.
        """
        logging.info(f"Updating match {match_id} (finish: {finish})")

        match_json = self.api.get_match(match_id)
        match = json.loads(json.dumps(match_json), object_hook=lambda dictionary: SimpleNamespace(**dictionary))
        
        fotmob_match = self.fotmob_service.get_match(match.whoscoredId)
        fotmob_match.match_id = match.id
        fotmob_match_json = fotmob_match.to_json(ensure_ascii=False)

        match_data = json.loads(fotmob_match_json)

        directory = match_data_directory.format(
            season=match.matchWeek.season.name,
            match_week_number=f"{match.matchWeek.matchWeekNumber:02}"
        )

        file_name = f"{match.homeTeam.name} vs {match.awayTeam.name} ({fotmob_match.elapsed.replace('/', '')}).json"
        full_path = os.path.join(directory, file_name)

        os.makedirs(directory, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump({
                "matchData": match_data,
                "finish": finish
        }, f, ensure_ascii=False, indent=2)
        
        self.d11_mq_sender.send_update_match_message(match_data, finish)
        logging.info(f"Match data for {match_id} sent to MQ")


    def update_player_photos(self, photo_directory, competition_id, season):
        """
        Updates player photos by fetching them from the Premier League API.
        """

        download_directory = os.getenv('PREMIER_LEAGUE_PHOTO_DIRECTORY', 'data/premier-league/photo/')
        temp_directory = download_directory + "temp"
        updated_directory = download_directory + "updated"
        new_directory = download_directory + "new"
        unknown_directory = download_directory + "unknown"

        photo_file_name_format = "{id}.png"

        if os.path.exists(download_directory):
            shutil.rmtree(download_directory)

        os.makedirs(temp_directory)
        os.makedirs(updated_directory)
        os.makedirs(new_directory)
        os.makedirs(unknown_directory)        

        for team in self.premier_league_service.get_teams(competition_id, season):
            logging.info(f"{team.name}")

            players = self.premier_league_service.get_players(competition_id, season, team.stat_source_id)
            for player in players:
                image = self.premier_league_service.download_player_photo(player.id)

                if image is None:
                    # No photo was found on PremierLeague.com
                    logging.info(f"    {player.name.display}: Photo not found")
                else:
                    # Download the file to the temp directory and name it with the Premier League player id
                    temp_file_name = photo_file_name_format.format(id = player.id)

                    with open(temp_directory + "/" + temp_file_name, "wb") as image_file:
                        image_file.write(image)

                    # Find a player with the Premier League id in the D11 API
                    d11_player_json = self.api.get_player_by_premier_league_id(player.id)

                    if d11_player_json is None:
                        # No player with the Premier League id was found in the D11 API
                        logging.info(f"    {player.name.display}: Unknown")
                        os.rename(temp_directory + "/" + temp_file_name,
                                  unknown_directory + "/" + temp_file_name)
                    else:
                        d11_player = json.loads(json.dumps(d11_player_json), object_hook=lambda dictionary: SimpleNamespace(**dictionary))
                        # A player with the Premier League id was found in the D11 API. Name the final result file
                        # with the D11 API player id
                        file_name = photo_file_name_format.format(id = d11_player.id)

                        if os.path.exists(photo_directory + "/" + file_name):
                            # A photo of the player already exists in the D11 application. Get the md5 of both
                            # the new and the existing file
                            temp_md5 = self.get_md5(temp_directory + "/" + temp_file_name)
                            existing_md5 = self.get_md5(photo_directory + "/" + file_name)

                            if temp_md5 == existing_md5:
                                # The new photo is the same as the already existing photo. Delete the temp file
                                os.remove(temp_directory + "/" + temp_file_name)
                                logging.info(f"    {d11_player.name}: Delete")
                            else:
                                # The new photo is not the same as the already existing photo.
                                # Move the file to the updated directory
                                os.rename(temp_directory + "/" + temp_file_name,
                                          updated_directory + "/" + file_name)
                                logging.info(f"    {d11_player.name}: Update")
                        else:
                            # A photo of the player does not already exist in the D11 application.
                            # Move the file to the new directory
                            os.rename(temp_directory + "/" + temp_file_name,
                                      new_directory + "/" + file_name)
                            logging.info(f"    {d11_player.name}: New")


    def get_md5(self, filename):
        """
        Computes the MD5 hash of a file.
        """
        with open(filename, "rb") as file:
            data = file.read()
            md5 = hashlib.md5(data).hexdigest()
            return md5