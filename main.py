import os
import sys
import argparse
import subprocess

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logging.getLogger("stomp").setLevel(logging.WARNING)

from dotenv import load_dotenv
load_dotenv()

from tkinter.filedialog import askdirectory, askopenfilename

from d11 import D11Service, D11Daemon
from fotmob import FotmobService

commands = [ 
    { "name": "hello", "description": "Prints a greeting", "arguments": []},
    { "name": "d11_daemon", "description": "Starts the D11 deamon that runs the scheduler and MQ listener", "arguments": []},
    { "name": "update_squads", "description": "Triggers a team squad update", "arguments": [] }, 
    { "name": "update_photos", "description": "Update player photos from PremierLeague.com", "arguments": [] }, 
    { "name": "update_match", "description": "Triggers a match update", "arguments": [ 
            { "name": "--match_id", "type": int, "required": True, "help": "Match ID"},
            { "name": "--finish", "action": "store_true", "required": False, "help": "Finish the match"},
        ] 
    },
    { "name": "export_fotmob_har", "description": "Runs the export_har.scpt to get a .har file that can be parsed", "arguments": [
            { "name": "--url", "type": str, "required": True, "help": "Output file path for the .har file"}
    ]},
    { "name": "parse_fotmob_har", "description": "Parses a .har file from Fotmob and updates the token in .fotmob_api_token", "arguments": []},
    { "name": "update_fotmob_token", "description": "Updates the Fotmob API token using Selenium", "arguments": []},
    { "name": "update_fotmob_ids", "description": "Generates SQL for updating missing Fotmob player ids", "arguments": []},
    { "name": "generate_pl_fixtures", "description": "Generates Premier League fixtures for the upcoming season", "arguments": []},
    { "name": "generate_d11_fixtures", "description": "Generates D11 fixtures for the upcoming season", "arguments": []},    
]

def main():

    parser = argparse.ArgumentParser(description="D11 Python")
    subparsers = parser.add_subparsers(dest="command")

    for command in commands:
        subparser = subparsers.add_parser(command["name"], help=command["description"])
        
        for argument in command["arguments"]:
            if "action" in argument:
                subparser.add_argument(argument["name"], action=argument["action"], required=argument.get("required", False), help=argument["help"])
            else:
                subparser.add_argument(argument["name"], type=argument["type"], required=argument["required"], help=argument["help"])

    if len(sys.argv) <= 1 or sys.argv[1] not in [command["name"] for command in commands]:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()

    if args.command == "hello":
        logging.info("Hello, World!")
    elif args.command == "d11_daemon":
        d11_daemon = D11Daemon()
        d11_daemon.start()
    elif args.command == "update_squads":
        competition_id = os.getenv('PREMIER_LEAGUE_DEFAULT_COMPETITION_ID')
        season = os.getenv('PREMIER_LEAGUE_DEFAULT_SEASON')

        if competition_id is None or season is None:
            logging.error("Competition id or season is not defined in .env")
            sys.exit(1)
        d11_service = D11Service()
        d11_service.update_squads(competition_id, season)
    elif args.command == "update_photos":
        photo_directory = askdirectory(initialdir = '.')

        if photo_directory == "":
            sys.exit();

        competition_id = os.getenv('PREMIER_LEAGUE_DEFAULT_COMPETITION_ID')
        season = os.getenv('PREMIER_LEAGUE_DEFAULT_SEASON')

        if competition_id is None or season is None:
            logging.error("Competition id or season is not defined in .env")
            sys.exit(1)
        
        d11_service = D11Service()
        d11_service.update_player_photos(photo_directory=photo_directory, competition_id=competition_id, season=season)
    elif args.command == "update_match":
        d11_service = D11Service()
        d11_service.update_match(args.match_id, args.finish)
    elif args.command == "export_fotmob_har":
        subprocess.run(["osascript", "./export_har/export-har.scpt", args.url])
    elif args.command == "parse_fotmob_har":
        file_path = os.getenv('FOTMOB_HAR_FILE_PATH')
        fotmob_service = FotmobService()
        fotmob_service.parse_fotmob_har(file_path)
    elif args.command == "update_fotmob_token": 
        fotmob_service = FotmobService()
        fotmob_service.get_fotmob_api_token()
    elif args.command == "update_fotmob_ids":
        league_id = os.getenv('FOTMOB_DEFAULT_LEAGUE_ID')

        if league_id is None:
            logging.error("League id is not defined in .env")
            sys.exit(1)

        id_file_name = askopenfilename(initialdir= '.')

        if id_file_name == "":
            sys.exit();
    
        fotmob_service = FotmobService()
        fotmob_service.generate_missing_player_ids(league_id, id_file_name)
    elif args.command == "generate_d11_fixtures":
        d11_service = D11Service()
        d11_service.generate_d11_fixtures()
    elif args.command == "generate_pl_fixtures":
        league_id = os.getenv('FOTMOB_DEFAULT_LEAGUE_ID')

        if league_id is None:
            logging.error("League id is not defined in .env")
            sys.exit(1)

        fotmob_service = FotmobService()
        fotmob_service.generate_pl_fixtures(league_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()