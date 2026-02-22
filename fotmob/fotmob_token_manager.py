import os
import re
import json
import base64
import hashlib
import logging
import random

from datetime import datetime, timezone
from threading import Lock
from typing import Dict, Any

# This is the static seed used in the JS token generation
h = """[Spoken Intro: Alan Hansen & Trevor Brooking]
I think it's bad news for the English game
We're not creative enough, and we're not positive enough

[Refrain: Ian Broudie & Jimmy Hill]
It's coming home, it's coming home, it's coming
Football's coming home (We'll go on getting bad results)
It's coming home, it's coming home, it's coming
Football's coming home
It's coming home, it's coming home, it's coming
Football's coming home
It's coming home, it's coming home, it's coming
Football's coming home

[Verse 1: Frank Skinner]
Everyone seems to know the score, they've seen it all before
They just know, they're so sure
That England's gonna throw it away, gonna blow it away
But I know they can play, 'cause I remember

[Chorus: All]
Three lions on a shirt
Jules Rimet still gleaming
Thirty years of hurt
Never stopped me dreaming

[Verse 2: David Baddiel]
So many jokes, so many sneers
But all those "Oh, so near"s wear you down through the years
But I still see that tackle by Moore and when Lineker scored
Bobby belting the ball, and Nobby dancing

[Chorus: All]
Three lions on a shirt
Jules Rimet still gleaming
Thirty years of hurt
Never stopped me dreaming

[Bridge]
England have done it, in the last minute of extra time!
What a save, Gordon Banks!
Good old England, England that couldn't play football!
England have got it in the bag!
I know that was then, but it could be again

[Refrain: Ian Broudie]
It's coming home, it's coming
Football's coming home
It's coming home, it's coming home, it's coming
Football's coming home
(England have done it!)
It's coming home, it's coming home, it's coming
Football's coming home
It's coming home, it's coming home, it's coming
Football's coming home

[Chorus: All]
(It's coming home) Three lions on a shirt
(It's coming home, it's coming) Jules Rimet still gleaming
(Football's coming home
It's coming home) Thirty years of hurt
(It's coming home, it's coming) Never stopped me dreaming
(Football's coming home
It's coming home) Three lions on a shirt
(It's coming home, it's coming) Jules Rimet still gleaming
(Football's coming home
It's coming home) Thirty years of hurt
(It's coming home, it's coming) Never stopped me dreaming
(Football's coming home
It's coming home) Three lions on a shirt
(It's coming home, it's coming) Jules Rimet still gleaming
(Football's coming home
It's coming home) Thirty years of hurt
(It's coming home, it's coming) Never stopped me dreaming
(Football's coming home)"""

# Configurable token TTL (default 5 hours)
TOKEN_TTL_SECONDS = int(os.getenv("FOTMOB_API_TOKEN_TTL", 5 * 3600))

class FotmobTokenManager:
    """
    A class to generate and cache Fotmob API tokens. Starting August 2025, tokens must be generated locally, 
    replicating the logic from Fotmob's frontend JavaScript.
    """

    __slots__ = ("tokens", "lock", "foo")

    def __init__(self, foo: str = None):
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
        # Allow direct injection for testing; otherwise use env var
        self.foo = foo or os.getenv("FOTMOB_API_TOKEN_FOO")
        
        if not self.foo:
            raise RuntimeError(
                "Environment variable FOTMOB_API_TOKEN_FOO is required but not set."
            )

    def get_token(self, url: str = None) -> str:
        """
        Returns a hopefully valid token.
        """
        # If we figure out the token generation logic, we can use get_generated_token here instead
        return self.read_token()
    
    def read_token(self) -> str:
        """
        Reads a token that hopefully has been aquired from the Fotmob frontend from .fotmob_.api_token
        """
        with open(".fotmob_api_token", "r") as f:
            return f.read().strip()

    def get_fotmob_cookies(self) -> str:
        """
        Returns hopefully valid Fotmob cookies.
        """
        return self.read_fotmob_cookies()

    def read_fotmob_cookies(self) -> str:
        """
        Reads fotmob cookies that hopefully have been acquired from the Fotmob frontend from .fotmob_cookies
        """
        with open('.fotmob_cookies', 'r') as f:
            lines = f.readlines()
            # Remove comment lines
            lines = [line for line in lines if not line.strip().startswith('#')]
            text = ''.join(lines)
            # Replace single-quoted values with double-quoted and escape inner double quotes
            def fix_quotes(match):
                value = match.group(1)
                value = value.replace('"', '\\"')
                return f': "{value}"'
            text = re.sub(r':\s*\'([^\']*)\'', fix_quotes, text)
            cookies = json.loads(text)        
            return cookies

    def get_generated_token(self, url: str) -> Dict[str, Any]:
        """
        Returns a valid token for the given URL. Caches tokens and regenerates if expired.
        """
        with self.lock:
            token_info = self.tokens.get(url)
            now = datetime.now(timezone.utc).timestamp()
            if not token_info or token_info["expires_at"] < now:
                logging.info(f"Generating new token for {url}")
                token_info = {
                    "token": self.generate_token(url),
                    # Adds slight randomization to avoid mass expiry
                    "expires_at": now + TOKEN_TTL_SECONDS + random.randint(-60, 60)
                }
                self.tokens[url] = token_info
            return token_info

    def generate_token(self, url: str) -> str:
        """
        Generates a Fotmob API token that matches the behavior of the site's JavaScript.
        This has stopped working but we'll keep it here if we want to keep working on it.
        
        The token is essentially:
        1. A JSON object with:
            - url: The request URL
            - code: A millisecond timestamp
            - foo: A secret key from the environment
        2. A signature generated by taking the MD5 (uppercase) of the JSON + lyrics string h
        3. The final token is a Base64-encoded JSON containing both the body and the signature
        """
        # Current UTC time (timezone-aware)
        date = datetime.now(timezone.utc)

        # Build the 'body' part of the token
        r = {
            "url": url,
            "code": int(date.timestamp() * 1000),
            "foo": self.foo
        }

        # Convert 'body' to compact JSON string
        r_json = json.dumps(r, separators=(',', ':'))

        # Concatenate body JSON with the lyrics string, then take uppercase MD5 hash
        signature = self.to_upper_md5(r_json + h)

        # Build final token object
        token_obj = {
            "body": r,
            "signature": signature
        }

        # Convert token object to JSON and Base64-encode
        token_json = json.dumps(token_obj, separators=(',', ':'))
        token_b64 = base64.b64encode(token_json.encode('utf-8')).decode('utf-8')

        return token_b64

    @staticmethod
    def to_upper_md5(data: str) -> str:
        """Returns uppercase MD5 hash of input string."""
        return hashlib.md5(data.encode('utf-8')).hexdigest().upper()

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decodes a token back to its JSON structure."""
        if not isinstance(token, str):
            raise TypeError("Token must be a Base64 string.")
        decoded = base64.b64decode(token).decode("utf-8")
        return json.loads(decoded)
