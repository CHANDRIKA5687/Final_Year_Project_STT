import sqlite3

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    
    return conn

def create_search_history_table(conn):
    """Create a table to store search history"""
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS search_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      sr_number INTEGER,
                      search_type TEXT NOT NULL,
                      transcribed_text TEXT NOT NULL)''')
    except sqlite3.Error as e:
        print(e)

def add_to_history(conn, search_type, text):
    """Insert search type and transcribed text into the search history table"""
    try:
        c = conn.cursor()
        c.execute("INSERT INTO search_history (sr_number, search_type, transcribed_text) VALUES (NULL, ?, ?)", (search_type, text))
        conn.commit()
    except sqlite3.Error as e:
        print(e)

def get_search_history(conn):
    """Retrieve search history from the database"""
    try:
        c = conn.cursor()
        c.execute("SELECT search_type, transcribed_text FROM search_history")
        rows = c.fetchall()
        return [f"{row[0]}:{row[1]}" for row in rows]
    except sqlite3.Error as e:
        print(e)
