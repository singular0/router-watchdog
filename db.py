"""Events database."""

import sqlite3


class DB:
    """Events database class."""

    def __init__(self, *, db_path: str):
        """
        Construct events database class.

        Parameters:
            db_path (str): path to database file
        """
        self._db_path = db_path
        self._create()

    def get_con(self):
        """
        Get database connection.

        Returns:
            new database connection
        """
        return sqlite3.connect(self._db_path)

    def _create(self):
        con = self.get_con()
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS events ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                    "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, "
                    "type VARCHAR(16) NOT NULL)")

    def save_event(self, event_type):
        """
        Save new event.

        Parameters:
            event_type (str): event type
        """
        con = self.get_con()
        cur = con.cursor()
        cur.execute("INSERT INTO events (type) VALUES (?)", [event_type])
        con.commit()
