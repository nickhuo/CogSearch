from __future__ import annotations

from flask import session

from ..db import get_db_connection


def format_pass_id(subtopID: int, conID: int, passOrder: int) -> str:
    """Construct 6-digit passID with proper formatting."""
    return f"{int(subtopID):03d}{int(conID):01d}{int(passOrder):02d}"


def save_pass_answer(
    qid: str,
    ans_to_save: str,
    table: str = "tb5_passQop",
    pass_id: str | None = None,
) -> None:
    """Persist c1/c2/c3/c4 answers using current session context.

    `pass_id` can be provided explicitly to avoid relying on the session state,
    which may have already advanced to the next passage by the time this runs.
    """
    uid = session.get("uid")
    sid = session.get("sid", "")
    passID = pass_id or session.get("passID", "")
    top_id = session.get("topID", 1)
    if table == "tb15_prac_passQop":
        top_id = session.get("practice_topID", top_id)

    if not passID:
        print("save_pass_answer warning: passID missing; skipping save")
        return

    link = None
    try:
        link = get_db_connection()
        cursor = link.cursor()

        if qid == "c1":
            if table == "tb15_prac_passQop":
                query = f"""
                    INSERT INTO {table}
                    (uid, sid, topID, subtopID, conID, passID, passOrder, c1Ans, c2Ans, c3Ans, c4Ans, passRT)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(
                    query,
                    (
                        uid,
                        sid,
                        top_id,
                        session.get("subtopID", 0),
                        session.get("conID", 1),
                        passID,
                        session.get("passOrder", 0),
                        ans_to_save,
                        0,
                        0,
                        0,
                        0,
                    ),
                )
            else:
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
                        top_id,
                        session.get("subtopID", 0),
                        session.get("conID", 1),
                        passID,
                        session.get("passOrder", 0),
                        ans_to_save,
                    ),
                )
        elif qid in ["c2", "c3", "c4"]:
            col = f"{qid}Ans"
            # First, attempt to update. This may affect 0 rows if the record doesn't exist
            # OR if the value is unchanged. We cannot rely on rowcount to detect existence.
            cursor.execute(
                f"""
                UPDATE {table}
                SET {col} = %s
                WHERE sid = %s AND uid = %s AND passID = %s
                """,
                (ans_to_save, sid, uid, passID),
            )

            # Determine whether the target record exists regardless of whether the value changed
            cursor.execute(
                f"SELECT 1 FROM {table} WHERE sid=%s AND uid=%s AND passID=%s LIMIT 1",
                (sid, uid, passID),
            )
            exists = cursor.fetchone() is not None

            if not exists:
                # No existing row; insert a new one with sensible defaults
                subtop_val = session.get("subtopID")
                con_val = session.get("conID")
                pass_order_val = session.get("passOrder")

                if not subtop_val and passID and passID[:3].isdigit():
                    subtop_val = int(passID[:3])
                if not con_val and passID and passID[3:4].isdigit():
                    con_val = int(passID[3:4])
                if (pass_order_val is None or pass_order_val == "") and passID and passID[4:].isdigit():
                    pass_order_val = int(passID[4:])

                subtop_str = str(subtop_val or 0)
                con_str = str(con_val or 1)
                pass_order_str = str(pass_order_val or 0)

                default_c1 = default_c2 = default_c3 = default_c4 = 0
                if qid == "c2":
                    default_c2 = ans_to_save
                elif qid == "c3":
                    default_c3 = ans_to_save
                elif qid == "c4":
                    default_c4 = ans_to_save

                if table == "tb15_prac_passQop":
                    cursor.execute(
                        f"""
                        INSERT INTO {table}
                            (uid, sid, topID, subtopID, conID, passID, passOrder,
                             c1Ans, c2Ans, c3Ans, c4Ans, passRT)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            uid,
                            sid,
                            top_id,
                            subtop_str,
                            con_str,
                            passID,
                            pass_order_str,
                            default_c1,
                            default_c2,
                            default_c3,
                            default_c4,
                            0,
                        ),
                    )
                else:
                    cursor.execute(
                        f"""
                        INSERT INTO {table}
                            (uid, sid, topID, subtopID, conID, passID, passOrder,
                             c1Ans, c2Ans, c3Ans, c4Ans, passRT)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            uid,
                            sid,
                            top_id,
                            subtop_str,
                            con_str,
                            passID,
                            pass_order_str,
                            0,
                            default_c2,
                            default_c3,
                            default_c4,
                            0,
                        ),
                    )

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
