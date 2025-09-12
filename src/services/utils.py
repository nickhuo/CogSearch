from __future__ import annotations

from flask import session

from ..db import get_db_connection


def format_pass_id(subtopID: int, conID: int, passOrder: int) -> str:
    """Construct 6-digit passID with proper formatting."""
    return f"{int(subtopID):03d}{int(conID):01d}{int(passOrder):02d}"


def save_pass_answer(qid: str, ans_to_save: str, table: str = "tb5_passQop") -> None:
    """Persist c1/c2/c3/c4 answers using current session context."""
    uid = session.get("uid")
    sid = session.get("sid", "")
    passID = session.get("passID", "")

    link = None
    try:
        link = get_db_connection()
        cursor = link.cursor()

        if qid == "c1":
            query = f"""
                INSERT INTO {table}
                (uid, sid, topID, subtopID, conID, passID, passOrder, c1Ans)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    uid,
                    sid,
                    session.get("topID", 1),
                    session.get("subtopID", 0),
                    session.get("conID", 1),
                    passID,
                    session.get("passOrder", 0),
                    ans_to_save,
                ),
            )
        elif qid in ["c2", "c3", "c4"]:
            col = f"{qid}Ans"
            query = f"""
                UPDATE {table}
                SET {col} = %s
                WHERE sid = %s AND uid = %s AND passID = %s
            """
            cursor.execute(query, (ans_to_save, sid, uid, passID))

        link.commit()
    except Exception as e:
        print(f"Error in save_pass_answer: {e}")
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()


def list_order(input_string: str, number: int):
    tasks = []
    for _ in range(number):
        cur_pos = input_string.find("#")
        tasks.append(input_string[:cur_pos])
        input_string = input_string[cur_pos + 1 :]
    return tasks


def split_subtopics(visited_sub_str: str):
    return visited_sub_str.split(",") if visited_sub_str else []
