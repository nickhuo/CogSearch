import mysql.connector
import time
from flask import current_app


def get_db_connection():
    """Create a new DB connection using Flask config."""
    connection_args = {
        "host": current_app.config.get("MYSQL_HOST", "localhost"),
        "user": current_app.config.get("MYSQL_USER", "root"),
        "password": current_app.config.get("MYSQL_PASSWORD", ""),
        "database": current_app.config.get("MYSQL_DB", "cogsearch_textsearch3"),
    }

    # Only set auth_plugin if explicitly provided in config to avoid mismatches
    auth_plugin = current_app.config.get("MYSQL_AUTH_PLUGIN")
    if auth_plugin:
        connection_args["auth_plugin"] = auth_plugin

    return mysql.connector.connect(**connection_args)


def get_time_stamp_cdt():
    """
    Equivalent to gmdate("Y-m-d H:i:s", time()-3600*5) => Central Daylight Time (UTC-5).
    """
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() - 3600*5))


def save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, url):
    try:
        link = get_db_connection()
        cursor = link.cursor()
        time_stamp = get_time_stamp_cdt()
        unix_time = int(time.time())
        insert_query = """
            INSERT INTO output1_url
                (uid, sid, topID, subtopID, conID, passID, pageTypeID,
                 time_stamp, unixTime, time_interval, url, pageTitle)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (
                uid,
                sid,
                topID,
                subtopID,
                conID,
                passID,
                pageTypeID,
                time_stamp,
                unix_time,
                0,
                url,
                pageTitle,
            ),
        )
        link.commit()
        return True
    except Exception as e:
        print(f"DB Error in save_url: {e}")
        return False
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()
