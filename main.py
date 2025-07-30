import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)

import sys
import argparse
from dotenv import load_dotenv

commands = [ 
    { "name": "hello", "description": "Prints a greeting" } 
]

def main():

    load_dotenv()

    parser = argparse.ArgumentParser(description="D11 Python")
    subparsers = parser.add_subparsers(dest="command")

    for command in commands:
        subparsers.add_parser(command["name"], help=command["description"])

    if len(sys.argv) <= 1 or sys.argv[1] not in [command["name"] for command in commands]:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()

    if args.command == "hello":
        logging.info("Hello, World!")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()