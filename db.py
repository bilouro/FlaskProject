import psycopg2
import psycopg2.extras
from flask import current_app


def get_connection():
    """
    Open a new PostgreSQL connection using configuration from Flask app.

    Uses current_app.config[...] values, which are set by the Config classes.
    """
    cfg = current_app.config
    conn = psycopg2.connect(
        host=cfg["DB_HOST"],
        port=cfg["DB_PORT"],
        dbname=cfg["DB_NAME"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
    )
    return conn


# Helper alias for row factory
RealDictCursor = psycopg2.extras.RealDictCursor