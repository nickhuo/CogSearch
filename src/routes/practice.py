from __future__ import annotations

import time
from flask import Blueprint, redirect, render_template, request, session, url_for

from src.db import get_db_connection, get_time_stamp_cdt, save_url
from src.services.utils import format_pass_id, save_pass_answer, split_subtopics


practice_bp = Blueprint("practice", __name__)


PRACTICE_REQUIRED_STAGES = {"c1", "c2", "c3", "c4"}


def _ensure_practice_top_id(cursor):
    """Return the configured practice topID, querying once per session."""
    top_id = session.get("practice_topID")
    if top_id:
        return top_id

    cursor.execute("SELECT topID FROM tb12_prac_topic ORDER BY topID LIMIT 1")
    row = cursor.fetchone()
    if isinstance(row, dict):
        top_id = row.get("topID")
    elif row:
        top_id = row[0]
    else:
        top_id = None

    top_id = str(top_id or "1")
    session["practice_topID"] = top_id
    return top_id


def _get_visited_subtopics() -> list[str]:
    subs = [sub for sub in split_subtopics(session.get("visitedSub", "")) if sub]
    return list(dict.fromkeys(subs))


def _practice_pending_redirect():
    """Return the URL that leads the user back to the outstanding practice question."""
    stage = session.get("practice_pending_stage")
    if stage not in PRACTICE_REQUIRED_STAGES:
        return None

    fid = session.get("practice_pending_fid")
    subtop = session.get("subtopID")
    pass_order = session.get("passOrder")
    params = {}
    if subtop is not None:
        params["subtop"] = subtop
    if pass_order is not None:
        params["passOrd"] = pass_order

    if stage == "c1" and not fid:
        last_page = session.get("practice_last_page")
        if last_page:
            params["lastPage"] = last_page
        return url_for("practice.prac_b", **params)
    if stage == "c1":
        return url_for("practice.prac_c1", fid=fid)
    if stage == "c2":
        return url_for("practice.prac_c2", fid=fid or "same")
    if stage == "c3":
        return url_for("practice.prac_c3", fid=fid or "same")
    if stage == "c4":
        return url_for("practice.prac_c4", fid=fid or "same")
    return None


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
        _ensure_practice_top_id(cursor)

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

    is_c3_submission = request.method == "POST" and request.form.get("qid") == "c3"

    if not is_c3_submission:
        pending_redirect = _practice_pending_redirect()
        if pending_redirect:
            return redirect(pending_redirect)

    fid = request.args.get("fid", "")
    subtop_param = request.args.get("subtop", "")
    last_page = request.args.get("lastPage", "")

    link = None
    visited_subtop = []
    try:
        link = get_db_connection()
        cursor = link.cursor()
        practice_top_id = _ensure_practice_top_id(cursor)

        visited_subtop = _get_visited_subtopics()
        session["visitedSub"] = ",".join(visited_subtop)

        if fid == "begin":
            session["startUnixTime"] = int(time.time())
            session["startTimeStamp"] = get_time_stamp_cdt()
            session["remainingTime"] = 240
            session["lastPageSwitchUnixTime"] = int(time.time())
            session.pop("practice_pending_stage", None)
            session.pop("practice_pending_passID", None)
            session.pop("practice_pending_fid", None)
            session.pop("practice_last_page", None)

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
                    practice_top_id,
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
            current = _get_visited_subtopics()
            if subtop_param and subtop_param not in current:
                current.append(subtop_param)
            session["visitedSub"] = ",".join(current)
            visited_subtop = current

        cursor.execute(
            "SELECT * FROM tb13_prac_subtopic WHERE topID=%s ORDER BY subtopID",
            (practice_top_id,),
        )
        all_subtops = []
        subtopics = cursor.fetchall()
        for row in subtopics:
            all_subtops.append(str(row[0]))

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
            visited_subtop = sorted(_get_visited_subtopics())

            session.pop("practice_pending_stage", None)
            session.pop("practice_pending_passID", None)
            session.pop("practice_pending_fid", None)
            session.pop("practice_last_page", None)

            if visited_subtop == sorted(all_subtops):
                return redirect(url_for("practice.prac_k2", lastPage="c3"))

        link.commit()

        cursor.execute(
            "SELECT * FROM tb12_prac_topic WHERE topID=%s",
            (practice_top_id,),
        )
        topic_result = cursor.fetchone()

        pageTypeID = "prac_a"
        pageTitle = f"a Prac: {topic_result[1]}" if topic_result else "a Prac"
        save_url(uid, sid, "", "", "", "", pageTypeID, pageTitle, request.url)

        session["redirectPage"] = url_for("practice.prac_k2", lastPage="a")

        if not visited_subtop:
            visited_subtop = _get_visited_subtopics()

        subtop_ids = [str(row[0]) for row in subtopics]
        all_completed = set(subtop_ids).issubset(set(visited_subtop)) and bool(subtop_ids)
        return render_template(
            "practice/prac_a.html",
            topic_result=topic_result,
            subtopics=subtopics,
            visited_subtop=visited_subtop,
            session=session,
            all_completed=all_completed,
            next_section_url=url_for("practice.prac_k2", lastPage="a"),
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
    practice_top_id = session.get("practice_topID") or session.get("topID") or "1"

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

    is_c3_submission = request.method == "POST" and request.form.get("qid") == "c3"

    pending_stage = session.get("practice_pending_stage")
    pending_pass = session.get("practice_pending_passID")
    if not is_c3_submission and pending_stage in PRACTICE_REQUIRED_STAGES:
        if pending_stage != "c1" or pending_pass != passID:
            redirect_url = _practice_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)

    if not is_c3_submission:
        session["practice_pending_passID"] = passID
        session["practice_pending_stage"] = "c1"
        session["practice_pending_fid"] = None
        session["practice_last_page"] = lastPage
    else:
        session["practice_last_page"] = lastPage

    link = None
    passResult = None

    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)
        practice_top_id = _ensure_practice_top_id(cursor)

        # persist current passage context for downstream routes/templates
        session.update(
            {
                "subtopID": subtopID,
                "conID": conID,
                "passOrder": passOrderInt,
                "passID": passID,
                "nextPassOrder": next_pass_order,
                "topID": practice_top_id,
                "practice_topID": practice_top_id,
            }
        )

        # load practice passage; passOrder is zero-padded in DB
        cursor.execute(
            """
            SELECT * FROM tb14_prac_passage
            WHERE topID=%s AND subtopID=%s AND conID=%s AND CAST(passOrder AS UNSIGNED)=%s
            """,
            (
                practice_top_id,
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
                    practice_top_id,
                ),
            )

        # log page view
        pageTypeID = "prac_b"
        pageTitle = passResult["passTitle"] if passResult else "Prac: No Title"
        save_url(
            uid=uid,
            sid=sid,
            topID=practice_top_id,
            subtopID=str(subtopID),
            conID=str(conID),
            passID=passID,
            pageTypeID=pageTypeID,
            pageTitle=pageTitle,
            url=request.url,
        )

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
            if request.method == 'POST':
                session.pop("practice_pending_stage", None)
                session.pop("practice_pending_passID", None)
                session.pop("practice_pending_fid", None)
                session.pop("practice_last_page", None)
                ans_to_save = request.form.get('ans', '')
                passid_to_save = request.form.get('savepassid', '')
                if ans_to_save:
                    cursor.execute(
                        """
                        UPDATE tb15_prac_passQop
                        SET c3Ans=%s
                        WHERE sid=%s AND uid=%s AND passID=%s
                        """,
                        (ans_to_save, sid, uid, passid_to_save),
                    )
        elif lastPage == "c4":
            session["lastPageSwitchUnixTime"] = now
            session["redirectPage"] = url_for("practice.prac_c1", fid="done")
            # clear pending flow references after completing c4
            session.pop("practice_pending_stage", None)
            session.pop("practice_pending_passID", None)
            session.pop("practice_pending_fid", None)
            session.pop("practice_last_page", None)

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
    practice_top_id = session.get("practice_topID") or session.get("topID") or "1"
    conID = "1"
    nextPassOrder = session.get("nextPassOrder", 2)

    pending_stage = session.get("practice_pending_stage")
    pending_pass = session.get("practice_pending_passID")
    if pending_stage in PRACTICE_REQUIRED_STAGES:
        if pending_pass != passID or pending_stage != "c3":
            redirect_url = _practice_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)
    else:
        redirect_url = _practice_pending_redirect()
        if redirect_url:
            return redirect(redirect_url)

    if not fid:
        fid = session.get("practice_pending_fid", "same")
    else:
        session["practice_pending_fid"] = fid

    pageTypeID = "prac_c3"
    pageTitle = f"C3: {passTitle}"
    save_url(
        uid,
        sid,
        practice_top_id,
        str(subtopID),
        str(conID),
        passID,
        pageTypeID,
        pageTitle,
        request.url,
    )

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c3")
        if ans:
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            session["practice_pending_stage"] = "c4"
            return redirect(url_for("practice.prac_c4", fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("practice/prac_c3.html", fid=fid, passID=passID)


@practice_bp.route("/prac_c4", methods=["GET", "POST"])
def prac_c4():
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get("fid", "")
    passID = session.get("passID", "")
    subtopID = session.get("subtopID", "")
    passTitle = session.get("passTitle", "")
    practice_top_id = session.get("practice_topID") or session.get("topID") or "1"
    conID = "1"

    pending_stage = session.get("practice_pending_stage")
    pending_pass = session.get("practice_pending_passID")
    if pending_stage in PRACTICE_REQUIRED_STAGES:
        if pending_pass != passID or pending_stage != "c4":
            redirect_url = _practice_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)
    else:
        redirect_url = _practice_pending_redirect()
        if redirect_url:
            return redirect(redirect_url)

    if not fid:
        fid = session.get("practice_pending_fid", "same")

    next_pass_order = session.get("nextPassOrder", 1)
    if fid == "same":
        action_url = url_for(
            "practice.prac_b",
            subtop=subtopID,
            passOrd=next_pass_order,
            lastPage="c4",
        )
    elif fid == "back":
        action_url = url_for(
            "practice.prac_a",
            fid="back",
            subtop=subtopID,
            lastPage="c4",
        )
    elif fid == "done":
        action_url = url_for("practice.prac_k2", lastPage="c4")
    else:
        action_url = url_for("practice.prac_k2", lastPage="unknown")

    pageTypeID = "prac_c4"
    pageTitle = f"C4 Prac: {passTitle}"
    save_url(
        uid,
        sid,
        practice_top_id,
        str(subtopID),
        str(conID),
        passID,
        pageTypeID,
        pageTitle,
        request.url,
    )

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c4")
        if ans:
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            link = None
            cursor = None
            try:
                link = get_db_connection()
                cursor = link.cursor()
                cursor.execute(
                    """
                    UPDATE tb16_prac_taskTime
                    SET timeEnd=%s, timeEndStamp=%s
                    WHERE uid=%s AND sid=%s AND topID=%s
                    ORDER BY timeStart DESC LIMIT 1
                    """,
                    (
                        int(time.time()),
                        get_time_stamp_cdt(),
                        uid,
                        sid,
                        str(practice_top_id),
                    ),
                )
                link.commit()
            except Exception as e:
                if link:
                    link.rollback()
                print(f"Error updating practice completion time: {e}")
                return f"Database error: {e}", 500
            finally:
                if cursor:
                    cursor.close()
                if link and link.is_connected():
                    link.close()

            session.pop("practice_pending_stage", None)
            session.pop("practice_pending_passID", None)
            session.pop("practice_pending_fid", None)
            session.pop("practice_last_page", None)
            return redirect(action_url)
        else:
            return "No answer provided.", 400

    return render_template("practice/prac_c4.html", fid=fid)


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
    practice_top_id = session.get("practice_topID") or session.get("topID") or "1"
    conID = "1"

    pending_stage = session.get("practice_pending_stage")
    pending_pass = session.get("practice_pending_passID")
    if pending_stage in PRACTICE_REQUIRED_STAGES:
        if pending_pass != passID or pending_stage != "c1":
            redirect_url = _practice_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)
    else:
        session["practice_pending_passID"] = passID
        session["practice_pending_stage"] = "c1"

    if fid:
        session["practice_pending_fid"] = fid
    else:
        stored_fid = session.get("practice_pending_fid")
        if stored_fid:
            fid = stored_fid

    pageTypeID = "prac_c1"
    pageTitle = f"C1 Prac: {passTitle}"
    save_url(
        uid,
        sid,
        practice_top_id,
        str(subtopID),
        str(conID),
        passID,
        pageTypeID,
        pageTitle,
        request.url,
    )

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c1")
        if ans:
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            session["practice_pending_stage"] = "c2"
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
    practice_top_id = session.get("practice_topID") or session.get("topID") or "1"
    conID = "1"

    pending_stage = session.get("practice_pending_stage")
    pending_pass = session.get("practice_pending_passID")
    if pending_stage in PRACTICE_REQUIRED_STAGES:
        if pending_pass != passID or pending_stage != "c2":
            redirect_url = _practice_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)
    else:
        redirect_url = _practice_pending_redirect()
        if redirect_url:
            return redirect(redirect_url)

    if not fid:
        fid = session.get("practice_pending_fid", "same")

    pageTypeID = "prac_c2"
    pageTitle = f"C2 Prac: {passTitle}"
    save_url(
        uid,
        sid,
        practice_top_id,
        str(subtopID),
        str(conID),
        passID,
        pageTypeID,
        pageTitle,
        request.url,
    )

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c2")
        if ans:
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            session["practice_pending_stage"] = "c3"
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

    is_c3_submission = request.method == "POST" and request.form.get("qid") == "c3"

    if not is_c3_submission:
        pending_redirect = _practice_pending_redirect()
        if pending_redirect:
            return redirect(pending_redirect)

    practice_top_id = session.get("practice_topID") or session.get("topID") or "1"
    lastPage = request.args.get("lastPage", "")

    link = None
    topic_title = ""
    subtop_string = ""

    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)
        practice_top_id = _ensure_practice_top_id(cursor)

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
                session.pop("practice_pending_stage", None)
                session.pop("practice_pending_passID", None)
                session.pop("practice_pending_fid", None)
                session.pop("practice_last_page", None)

        cursor.execute(
            "SELECT * FROM tb12_prac_topic WHERE topID=%s",
            (practice_top_id,),
        )
        topic_row = cursor.fetchone()
        if topic_row:
            topic_title = topic_row["topTitle"]

        cursor.execute(
            "SELECT * FROM tb13_prac_subtopic WHERE topID=%s ORDER BY subtopID",
            (practice_top_id,),
        )
        subtop_rows = cursor.fetchall()
        subtop_list = [row["subtopTitle"] for row in subtop_rows]
        subtop_string = ", ".join(subtop_list)

        pageTypeID = "prac_k2"
        pageTitle = f"K2 Prac: {topic_title}"
        save_url(
            uid=uid,
            sid=sid,
            topID=practice_top_id,
            subtopID="",
            conID="",
            passID="",
            pageTypeID=pageTypeID,
            pageTitle=pageTitle,
            url=request.url,
        )

        link.commit()

    except Exception as e:
        print(f"Error in /prac_k2: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template("practice/prac_k2.html", topicTitle=topic_title, subtopString=subtop_string, lastPage=lastPage)
