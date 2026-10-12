import mysql.connector
from config import DB_CONFIG

def get_db_connection():
    """
    Establishes and returns a connection to the MySQL database
    using parameters configured in DB_CONFIG.
    """
    return mysql.connector.connect(**DB_CONFIG)