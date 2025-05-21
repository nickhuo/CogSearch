import mysql.connector
import time

def get_db_connection():
    """
    Returns a new DB connection (edit credentials as needed).
    """
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='cogsearch_textsearch3',
        auth_plugin='mysql_native_password'
    )
    # return mysql.connector.connect(
    #     host='localhost',
    #     user='cogsearch_write',
    #     password='Cog_Search34_Root',
    #     database='cogsearch_textsearch3'
    # )

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
        # Set time_interval to 0 since no default is defined.
        insert_query = """
            INSERT INTO output1_url
                (uid, sid, topID, subtopID, conID, passID, pageTypeID,
                 time_stamp, unixTime, time_interval, url, pageTitle)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            uid, sid, topID, subtopID, conID, passID, pageTypeID,
            time_stamp, unix_time, 0, url, pageTitle
        ))
        link.commit()
    except Exception as e:
        print(f"DB Error in save_url: {e}")
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

