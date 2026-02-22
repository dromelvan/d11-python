import sqlite3
import shutil
import tempfile
from pathlib import Path

FIREFOX_PROFILES_DIR = Path.home() / "Library/Application Support/Firefox/Profiles"

FOTMOB_HOST = "%fotmob.com%"
FOTMOB_NAME = "turnstile_verified"

class FotmobCookieManager:
    def safe_copy(self,db_path: Path):
        """
        Create a temporary copy of the given SQLite database, including its WAL file if it exists.
        """
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_db = tmp_dir / "cookies.sqlite"

        shutil.copy2(db_path, tmp_db)

        wal_src = db_path.with_name("cookies.sqlite-wal")
        if wal_src.exists():
            shutil.copy2(wal_src, tmp_db.with_name("cookies.sqlite-wal"))

        return tmp_dir, tmp_db

    def row_to_cookie(self, row):
        """
        Convert a database row to a cookie dictionary.
        """
        return {
            "host": row[0],
            "name": row[1],
            "value": row[2],
            "path": row[3],
            "expiry": row[4],
            "secure": bool(row[5]),
            "httpOnly": bool(row[6]),
        }


    def get_best_turnstile_cookie(self, conn):
        """
        Retrieve the best turnstile cookie from the given database connection.
        """
        cur = conn.cursor()

        cur.execute("""
            SELECT host, name, value, path, expiry, isSecure, isHttpOnly
            FROM moz_cookies
            WHERE host LIKE ?
            AND name = ?
        """, (FOTMOB_HOST, FOTMOB_NAME))

        rows = cur.fetchall()
        if not rows:
            return None

        # Prefer session cookie first
        session_cookies = [r for r in rows if r[4] == 0]
        if session_cookies:
            return session_cookies[0]

        # Otherwise pick newest expiry
        return max(rows, key=lambda r: r[4])


    def find_latest_turnstile_cookie(self):
        """
        Find the latest turnstile cookie across all Firefox profiles.
        """
        best_cookie = None
        best_expiry = -1

        for profile_dir in FIREFOX_PROFILES_DIR.iterdir():
            if not profile_dir.is_dir():
                continue

            db_path = profile_dir / "cookies.sqlite"
            if not db_path.exists():
                continue

            tmp_dir, safe_db = self.safe_copy(db_path)

            try:
                conn = sqlite3.connect(f"file:{safe_db}?mode=ro", uri=True)

                cookie = self.get_best_turnstile_cookie(conn)
                if cookie:
                    expiry = cookie[4]

                    if expiry == 0:
                        return self.row_to_cookie(cookie)

                    if expiry > best_expiry:
                        best_cookie = cookie
                        best_expiry = expiry

                conn.close()

            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        return self.row_to_cookie(best_cookie) if best_cookie else None