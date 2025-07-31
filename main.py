import os
import sys
import argparse

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)

from dotenv import load_dotenv
load_dotenv()

from d11 import D11Service

commands = [ 
    { "name": "hello", "description": "Prints a greeting", "arguments": []},
    { "name": "update_squads", "description": "Triggers a team squad update", "arguments": [] }, 
    { "name": "update_match", "description": "Triggers a match update", "arguments": [ 
            { "name": "--match_id", "type": int, "required": True, "help": "Match ID"},
            { "name": "--finish", "action": "store_true", "required": False, "help": "Finish the match"},
        ] 
    } 
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
    elif args.command == "update_squads":
        competition_id = os.getenv('PREMIER_LEAGUE_DEFAULT_COMPETITION_ID')
        season = os.getenv('PREMIER_LEAGUE_DEFAULT_SEASON')

        if competition_id is None or season is None:
            logging.error("Competition id or season is not defined in .env")
            sys.exit(1)
        d11_service = D11Service()
        d11_service.update_squads(competition_id, season)
    elif args.command == "update_match":
        d11_service = D11Service()
        d11_service.update_match(args.match_id, args.finish)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()