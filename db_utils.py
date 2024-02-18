from configparser import ConfigParser
from pathlib import Path
from typing import Dict
import psycopg2

DB_INIT_FILE = "database.ini"


def db_config(filename: Path = DB_INIT_FILE, section: str = 'postgresql') -> Dict[str, str]:
    parser = ConfigParser()
    parser.read(filename)
    if parser.has_section(section):
        params = parser.items(section)
        db = {
            param[0]: param[1] for param in params
        }
    else:
        raise Exception(f'Section {section} not found in the {filename} file')
    return db


def create_db_connection():
    params = db_config()
    try:
        conn = psycopg2.connect(**params)
        return conn
    except (Exception, psycopg2.Error) as error:
        print(f'Error while connecting {error}')
    return None


