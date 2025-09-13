from __future__ import annotations

import time
from flask import Blueprint, redirect, render_template, request, session, url_for

from src.db import get_db_connection, get_time_stamp_cdt, save_url
from src.services.utils import format_pass_id, save_pass_answer, split_subtopics


practice_bp = Blueprint("practice", __name__)


@practice_bp.route("/prac_instruction", methods=["POST"])
def prac_instruction():
    """Inserts demographic answers (if provided) then shows instructions."""
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    link = None
    try:
        link = get_db_connection()
        cursor = link.cursor()

        bmv = request.form.get("demog_bm")
        if bmv:
            bdv = request.form.get("demog_bd", "")
            byv = request.form.get("demog_by", "")
            bsv = f"{bmv}/{bdv}/{byv}"
            agev = request.form.get("demog_age", "")
            genv = request.form.get("demog_gen", "")
            eduv = request.form.get("demog_edu", "")
            natengv = request.form.get("demog_eng", "")
            firlanv = request.form.get("demog_firlan", "")
            ageengv = request.form.get("demog_ageeng", "")
            hislatv = request.form.get("demog_hislat", "")
            racev = request.form.get("demog_race", "")

            cursor.execute(
                """
                INSERT INTO tb11_profile (
                    uid, sid,
                    dobMonth, dobDay, dobYear, dobSum,
                    age, gender, edu, natEng, firLan,
                    ageEng, hisLat, race
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uid,
                    sid,
                    bmv,
                    bdv,
                    byv,
                    bsv,
                    agev,
                    genv,
                    eduv,
                    natengv,
                    firlanv,
                    ageengv,
                    hislatv,
                    racev,
                ),
            )
            link.commit()

        pageTypeID = "prac_instruction"
        pageTitle = "Prac: Instruction"
        save_url(uid, sid, "", "", "", "", pageTypeID, pageTitle, request.url)
        link.commit()

    except Exception as e:
        print(f"Error in /prac_instruction route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template("practice/prac_instruction.html")


@practice_bp.route("/prac_a", methods=["GET", "POST"])
def prac_a():
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get("fid", "")
    subtop_param = request.args.get("subtop", "")
    last_page = request.args.get("lastPage", "")

    link = None
    visited_subtop = []
    try:
        link = get_db_connection()
        cursor = link.cursor()

        if fid == "begin":
            session["startUnixTime"] = int(time.time())
            session["startTimeStamp"] = get_time_stamp_cdt()
            session["remainingTime"] = 300
            session["lastPageSwitchUnixTime"] = int(time.time())

            cursor.execute(
                """
                INSERT INTO tb16_prac_taskTime
                    (uid, sid, topID, timeStart, timeEnd, timeStartStamp, timeEndStamp)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uid,
                    sid,
                    "1",
                    session["startUnixTime"],
                    int(time.time()),
                    session["startTimeStamp"],
                    get_time_stamp_cdt(),
                ),
            )

            session["visitedSub"] = ""
            visited_subtop = []

        elif fid in ["back", "next"]:
            session["lastPageSwitchUnixTime"] = int(time.time())
            current = session.get("visitedSub", "")
            if current:
                session["visitedSub"] = current + "," + subtop_param
            else:
                session["visitedSub"] = subtop_param
            # Append to the local tracker without reassigning (append returns None)
            visited_subtop.append(subtop_param)

        cursor.execute("SELECT * FROM tb13_prac_subtopic WHERE topID=%s ORDER BY subtopID", ("1",))
        all_subtops = []
        subtopics = cursor.fetchall()
        for row in subtopics:
            all_subtops.append(row[0])

        if last_page == "c3" and request.method == "POST":
            ans = request.form.get("ans", "")
            passid_to_save = request.form.get("savepassid", "")
            if ans:
                cursor.execute(
                    """
                    UPDATE tb15_prac_passQop
                    SET c3Ans=%s
                    WHERE sid=%s AND uid=%s AND passID=%s
                    """,
                    (ans, sid, uid, passid_to_save),
                )
            visited_subtop = split_subtopics(session.get("visitedSub", ""))
            visited_subtop.sort()
            if visited_subtop == all_subtops:
                return redirect(url_for("practice.prac_k2", lastPage="c3"))

        link.commit()

        cursor.execute("SELECT * FROM tb12_prac_topic WHERE topID=%s", ("1",))
        topic_result = cursor.fetchone()

        pageTypeID = "prac_a"
        pageTitle = f"a Prac: {topic_result[1]}" if topic_result else "a Prac"
        save_url(uid, sid, "", "", "", "", pageTypeID, pageTitle, request.url)

        session["redirectPage"] = url_for("practice.prac_k2", lastPage="a")

        if not visited_subtop:
            visited_subtop = split_subtopics(session.get("visitedSub", ""))

        return render_template(
            "practice/prac_a.html",
            topic_result=topic_result,
            subtopics=subtopics,
            visited_subtop=visited_subtop,
            session=session,
        )

    except Exception as e:
        print(f"Error in /prac_a route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()


@practice_bp.route("/prac_b", methods=["GET", "POST"])
def prac_b():
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # query params
    subtopID = request.args.get("subtop", 0)
    passOrd = request.args.get("passOrd", 1)
    lastPage = request.args.get("lastPage", "")

    # normalize types
    try:
        subtopID = int(subtopID)
    except (TypeError, ValueError):
        subtopID = 0
    try:
        passOrderInt = int(passOrd)
    except (TypeError, ValueError):
        passOrderInt = 1

    conID = 1
    passID = format_pass_id(subtopID, conID, passOrderInt)
    next_pass_order = passOrderInt + 1

    # persist to session
    session.update(
        {
            "subtopID": subtopID,
            "conID": conID,
            "passOrder": passOrderInt,
            "passID": passID,
            "nextPassOrder": next_pass_order,
        }
    )

    link = None
    passResult = None

    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)

        # load practice passage; passOrder is zero-padded in DB
        cursor.execute(
            """
            SELECT * FROM tb14_prac_passage
            WHERE topID=%s AND subtopID=%s AND conID=%s AND CAST(passOrder AS UNSIGNED)=%s
            """,
            (
                "1",
                str(subtopID),
                str(conID),
                int(passOrderInt),
            ),
        )
        passResult = cursor.fetchone()
        if passResult and 'passTitle' in passResult:
            session['passTitle'] = passResult['passTitle']

        # when first article, set practical task start time
        if passOrderInt == 1:
            cursor.execute(
                """
                UPDATE tb16_prac_taskTime
                SET timeStart=%s, timeStartStamp=%s
                WHERE uid=%s AND sid=%s AND topID=%s
                ORDER BY timeStart DESC LIMIT 1
                """,
                (
                    int(time.time()),
                    get_time_stamp_cdt(),
                    uid,
                    sid,
                    "1",
                ),
            )

        # log page view
        pageTypeID = "prac_b"
        pageTitle = passResult["passTitle"] if passResult else "Prac: No Title"
        save_url(uid=uid, sid=sid, topID="1", subtopID=str(subtopID), conID=str(conID), passID=passID, pageTypeID=pageTypeID, pageTitle=pageTitle, url=request.url)

        # timing/redirect bookkeeping like core.task_b
        now = int(time.time())
        if lastPage == "a":
            used_time = now - session.get("lastPageSwitchUnixTime", now)
            session["remainingTime"] = session.get("remainingTime", 0) - used_time
            session["lastPageSwitchUnixTime"] = now
            session["redirectPage"] = url_for("practice.prac_c1", fid="done")
        elif lastPage == "c3":
            session["lastPageSwitchUnixTime"] = now
            session["redirectPage"] = url_for("practice.prac_c1", fid="done")

        link.commit()

    except Exception as e:
        print(f"Error in /prac_b route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template(
        "practice/prac_b.html",
        passResult=passResult,
        passOrder=passOrderInt,
        pageTitle=pageTitle if passResult else "Practice B",
    )


@practice_bp.route("/prac_c3", methods=["GET", "POST"])
def prac_c3():
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get("fid", "")
    subtopID = session.get("subtopID", "")
    passID = session.get("passID", "")
    passTitle = session.get("passTitle", "")
    topID = "1"
    conID = "1"
    nextPassOrder = session.get("nextPassOrder", 2)

    if fid == "same":
        action_url = url_for("practice.prac_b", subtop=subtopID, passOrd=nextPassOrder, lastPage="c3")
    elif fid == "back":
        action_url = url_for("practice.prac_a", fid="back", subtop=subtopID, lastPage="c3")
    elif fid == "done":
        action_url = url_for("practice.prac_k2", lastPage="c3")
    else:
        action_url = url_for("practice.prac_k2", lastPage="unknown")

    pageTypeID = "prac_c3"
    pageTitle = f"C3: {passTitle}"
    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c3")
        if ans:
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            return redirect(action_url)
        else:
            return "No answer provided.", 400

    return render_template("practice/prac_c3.html", fid=fid, action_url=action_url, passID=passID)


@practice_bp.route("/prac_c1", methods=["GET", "POST"])
def prac_c1():
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get("fid", "")
    subtopID = session.get("subtopID", "")
    passID = session.get("passID", "")
    passTitle = session.get("passTitle", "")
    topID = "1"
    conID = "1"

    pageTypeID = "prac_c1"
    pageTitle = f"C1 Prac: {passTitle}"
    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c1")
        if ans:
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            return redirect(url_for("practice.prac_c2", fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("practice/prac_c1.html", fid=fid)


@practice_bp.route("/prac_c2", methods=["GET", "POST"])
def prac_c2():
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get("fid", "")
    subtopID = session.get("subtopID", "")
    passID = session.get("passID", "")
    passTitle = session.get("passTitle", "")
    topID = "1"
    conID = "1"

    pageTypeID = "prac_c2"
    pageTitle = f"C2 Prac: {passTitle}"
    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c2")
        if ans:
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            return redirect(url_for("practice.prac_c3", fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("practice/prac_c2.html", fid=fid)

@practice_bp.route("/prac_k2", methods=["GET", "POST"])
def prac_k2():
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    topID = "1"
    lastPage = request.args.get("lastPage", "")

    link = None
    topic_title = ""
    subtop_string = ""

    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)

        if lastPage == "c3" and request.method == "POST":
            ans_to_save = request.form.get("ans", "")
            passid_to_save = request.form.get("savepassid", "")
            if ans_to_save:
                cursor.execute(
                    """
                    UPDATE tb15_prac_passQop
                    SET c3Ans=%s
                    WHERE sid=%s AND uid=%s AND passID=%s
                    """,
                    (ans_to_save, sid, uid, passid_to_save),
                )

        cursor.execute("SELECT * FROM tb12_prac_topic WHERE topID=%s", (topID,))
        topic_row = cursor.fetchone()
        if topic_row:
            topic_title = topic_row["topTitle"]

        cursor.execute("SELECT * FROM tb13_prac_subtopic WHERE topID=%s ORDER BY subtopID", (topID,))
        subtop_rows = cursor.fetchall()
        subtop_list = [row["subtopTitle"] for row in subtop_rows]
        subtop_string = ", ".join(subtop_list)

        pageTypeID = "prac_k2"
        pageTitle = f"K2 Prac: {topic_title}"
        save_url(uid=uid, sid=sid, topID=topID, subtopID="", conID="", passID="", pageTypeID=pageTypeID, pageTitle=pageTitle, url=request.url)

        link.commit()

    except Exception as e:
        print(f"Error in /prac_k2: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template("practice/prac_k2.html", topicTitle=topic_title, subtopString=subtop_string, lastPage=lastPage)
