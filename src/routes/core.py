from __future__ import annotations

import time
from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.db import get_db_connection, get_time_stamp_cdt, save_url
from src.services.utils import list_order, format_pass_id, save_pass_answer


LETTER_COMPARISON_ROUNDS = {
    1: [
        {"left": "PRDBZTYFN", "right": "PRDBZTYFN", "answer": "S"},
        {"left": "NCWJDZ", "right": "NCMJDZ", "answer": "D"},
        {"left": "KHW", "right": "KBW", "answer": "D"},
        {"left": "ZRBGMF", "right": "ZRBCMF", "answer": "D"},
        {"left": "BTH", "right": "BYH", "answer": "D"},
        {"left": "XWKQRYCNZ", "right": "XWKQRYCNZ", "answer": "S"},
        {"left": "HNPDLK", "right": "HNPDLK", "answer": "S"},
        {"left": "WMQTRSGLZ", "right": "WMQTRZGLZ", "answer": "D"},
        {"left": "JPN", "right": "JPN", "answer": "S"},
        {"left": "QLXSVT", "right": "QLNSVT", "answer": "D"},
    ],
    2: [
        {"left": "YXHKZVFPB", "right": "YXHKZVFPD", "answer": "D"},
        {"left": "RJZ", "right": "RJZ", "answer": "S"},
        {"left": "CLNPZD", "right": "CLNPZD", "answer": "S"},
        {"left": "DCBPFHXYJ", "right": "DCBPFHXYJ", "answer": "S"},
        {"left": "MWR", "right": "ZWR", "answer": "D"},
        {"left": "LPKXZW", "right": "LPKXZW", "answer": "S"},
        {"left": "TZL", "right": "TZQ", "answer": "D"},
        {"left": "CSDBFPHXZ", "right": "CSDBFPHXZ", "answer": "S"},
        {"left": "QHZXPC", "right": "QHZWPC", "answer": "D"},
        {"left": "JNWXHPFBD", "right": "JNWXHPFMD", "answer": "D"},
    ],
}


core_bp = Blueprint("core", __name__)


def safe_int_param(value, default=0):
    """Safely convert parameter to integer, handling empty strings and None values"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


FORMAL_REQUIRED_STAGES = {"c1", "c2", "c3", "c4"}


def _formal_pending_redirect():
    """Return the URL that routes the participant back to outstanding formal questions."""
    stage = session.get("formal_pending_stage")
    if stage not in FORMAL_REQUIRED_STAGES:
        return None

    fid = session.get("formal_pending_fid")
    subtop = session.get("subtopID")
    pass_order = session.get("passOrder")
    params = {}
    if subtop is not None:
        params["subtop"] = subtop
    if pass_order is not None:
        params["passOrd"] = pass_order

    if stage == "c1" and not fid:
        last_page = session.get("formal_last_page")
        if last_page:
            params["lastPage"] = last_page
        return url_for("core.task_b", **params)
    if stage == "c1":
        return url_for("core.task_c1", fid=fid)
    if stage == "c2":
        return url_for("core.task_c2", fid=fid or "same")
    if stage == "c3":
        return url_for("core.task_c3", fid=fid or "same")
    if stage == "c4":
        return url_for("core.task_c4", fid=fid or "same")
    return None


def _is_formal_rating_submission() -> bool:
    return request.method == "POST" and request.form.get("qid") in {"c3", "c4"}


@core_bp.route("/")
def index():
    return render_template("index.html")


@core_bp.route("/warning")
def warning():
    return render_template("warning.html")


@core_bp.route("/consent", methods=["GET"])
def consent():
    if "sid" in session:
        session.clear()
    return render_template("consent.html")


@core_bp.route("/demographic", methods=["POST"])
def demographic():
    # If a uid already exists, clear it
    if "uid" in session and session["uid"]:
        session["uid"] = ""

    participant_id = request.form.get("participant_id", "").strip()

    if not participant_id:
        error_message = "Participant ID is required."
        return render_template(
            "consent.html", error=error_message, participant_id=participant_id
        )

    if not participant_id.isdigit():
        error_message = "Participant ID must contain digits only."
        return render_template(
            "consent.html", error=error_message, participant_id=participant_id
        )

    sid = participant_id
    session["sid"] = sid

    link = None
    try:
        link = get_db_connection()
        cursor = link.cursor()

        timeStamp = get_time_stamp_cdt()

        cursor.execute(
            """
            INSERT INTO tb1_user 
                (sid, topIDorder, subtopIDorder, conIDorder, taskDone, conDone, signedConsent, signedDate)
            VALUES
                (%s, '', '', '', 0, 0, 'TRUE', %s)
            """,
            (sid, timeStamp),
        )

        cursor.execute("SELECT MAX(uid) FROM tb1_user WHERE sid=%s", (sid,))
        row = cursor.fetchone()
        if row and row[0]:
            session["uid"] = row[0]

        bmv = request.form.get("demog_bm", "").strip()
        if bmv:
            bdv = request.form.get("demog_bd", "").strip()
            byv = request.form.get("demog_by", "").strip()
            bsv = f"{bmv}/{bdv}/{byv}"
            agev = request.form.get("demog_age", "").strip()
            genv = request.form.get("demog_gen", "").strip()
            eduv = request.form.get("demog_edu", "").strip()
            natengv = request.form.get("demog_eng", "").strip()
            firlanv = request.form.get("demog_firlan", "").strip()
            ageengv = request.form.get("demog_ageeng", "").strip()
            hislatv = request.form.get("demog_hislat", "").strip()
            racev = request.form.get("demog_race", "").strip()

            cursor.execute(
                """
                INSERT INTO tb11_profile
                    (uid, sid, dobMonth, dobDay, dobYear, dobSum, age, gender, edu, natEng, firLan, ageEng, hisLat, race)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session["uid"],
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

        pageTypeID = "start_demog"
        pageTitle = "Start Demographic Information"
        save_url(session["uid"], sid, "", "", "", "", pageTypeID, pageTitle, request.url)

        link.commit()

    except Exception as e:
        print(f"DB Error in /demographic: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template("demographic.html")


@core_bp.route("/timer")
def timer_page():
    remaining_time = session.get("remainingTime", 0)
    redirect_page = session.get("redirectPage", "")
    return render_template("timer.html", remaining_time=remaining_time, redirect_page=redirect_page)


@core_bp.route("/set_timer")
def set_timer():
    session["remainingTime"] = 300
    session["redirectPage"] = "/done"
    return redirect(url_for("core.timer_page"))


@core_bp.route("/task_setting")
def task_setting():
    topID = request.args.get("topID", "unknown")
    return render_template("task_setting.html", topID=topID)


@core_bp.route("/settings")
def settings():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("core.index"))

    link = get_db_connection()
    try:
        cursor = link.cursor(dictionary=True)
        cursor.execute("SELECT topIDorder, taskDone FROM tb1_user WHERE uid = %s", (uid,))
        user_data = cursor.fetchone()
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    if not user_data:
        return "User data not found", 404

    topIDorder, taskDone = user_data.get("topIDorder"), user_data.get("taskDone")
    task_array = list_order(topIDorder, 1) if topIDorder else []
    current_topID = task_array[taskDone] if (isinstance(taskDone, int) and 0 <= taskDone < len(task_array)) else ""

    return render_template(
        "settings.html",
        current_topID=current_topID,
        user_id=uid,
        session_id=session.get("sid"),
    )


@core_bp.route("/save_url", methods=["POST"])
def handle_save_url():
    uid = session.get("uid")
    sid = request.form.get("sid", "")
    topID = request.form.get("topID", "")
    subtopID = request.form.get("subtopID", "")
    conID = request.form.get("conID", "")
    passID = request.form.get("passID", "")
    pageTypeID = request.form.get("pageTypeID", "")
    url_str = request.form.get("url", "")
    pageTitle = request.form.get("pageTitle", "")

    save_url(
        uid,
        sid,
        topID,
        subtopID,
        conID,
        passID,
        pageTypeID,
        pageTitle,
        url_str,
    )

    return jsonify({"status": "ok"}), 200


# --- Task (non-practice) routes kept under core for now ---

@core_bp.route("/instruction", methods=["GET", "POST"])
def instruction():
    uid = session.get("uid")
    sid = session.get("sid", "")
    if not uid:
        return "No user session found; please start from the beginning.", 400

    link = None
    topID = "1"
    try:
        link = get_db_connection()
        cursor = link.cursor()

        if request.method == "POST":
            ans_to_save = request.form.get("textarea_k2", "").strip()
            if ans_to_save:
                cursor.execute(
                    """
                    INSERT INTO tb18_prac_topicIdeas 
                        (uid, sid, topID, quesID, quesAns)
                    VALUES 
                        (%s, %s, %s, 'prac_k2', %s)
                    """,
                    (uid, sid, topID, ans_to_save),
                )

        strDomain = "01#"
        remain = uid % 6
        if remain == 1:
            strCon = "1#2#3#1#2#3#1#2#3#1#2#3#"
        elif remain == 2:
            strCon = "2#3#1#2#3#1#2#3#1#2#3#1#"
        elif remain == 3:
            strCon = "3#1#2#3#1#2#3#1#2#3#1#2#"
        elif remain == 4:
            strCon = "1#3#2#1#3#2#1#3#2#1#3#2#"
        elif remain == 5:
            strCon = "2#1#3#2#1#3#2#1#3#2#1#3#"
        else:
            strCon = "3#2#1#3#2#1#3#2#1#3#2#1#"

        cursor.execute(
            """
            UPDATE tb1_user
            SET topIDorder=%s, conIDorder=%s
            WHERE sid=%s AND uid=%s
            """,
            (strDomain, strCon, sid, uid),
        )

        pageTypeID = "instruction"
        pageTitle = "Instruction"
        session["topID"] = topID
        session.pop("practice_topID", None)
        save_url(uid=uid, sid=sid, topID=topID, subtopID="", conID="", passID="", pageTypeID=pageTypeID, pageTitle=pageTitle, url=request.url)
        link.commit()

    except Exception as e:
        print(f"Error in /instruction route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template("instruction.html")


# --- Non-practice task routes migrated from app.py ---

@core_bp.route('/task_a', methods=['GET', 'POST'])
def task_a():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    is_rating_submission = _is_formal_rating_submission()

    if not is_rating_submission:
        pending_redirect = _formal_pending_redirect()
        if pending_redirect:
            return redirect(pending_redirect)

    topID = "1"
    fid = request.args.get('fid', '')
    lastPage = request.args.get('lastPage', '')
    subtop_param = request.args.get('subtop', '')
    session['topID'] = topID

    link = None
    visited_subtop = []
    try:
        link = get_db_connection()
        cursor = link.cursor()

        if fid == "begin":
            session['startUnixTime'] = int(time.time())
            session['startTimeStamp'] = get_time_stamp_cdt()
            session['remainingTime'] = 900  
            session['lastPageSwitchUnixTime'] = int(time.time())
            session.pop('formal_pending_stage', None)
            session.pop('formal_pending_passID', None)
            session.pop('formal_pending_fid', None)
            session.pop('formal_last_page', None)

            # Insert start time row into tb6_taskTime
            cursor.execute(
                """
                INSERT INTO tb6_taskTime (uid, sid, topID, timeStart, timeEnd, timeStartStamp, timeEndStamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uid,
                    sid,
                    topID,
                    session['startUnixTime'],
                    int(time.time()),
                    session['startTimeStamp'],
                    get_time_stamp_cdt(),
                ),
            )
            session['visitedSub'] = ''
            visited_subtop = []

        elif fid in ["back", "next", "complete"]:
            session['lastPageSwitchUnixTime'] = int(time.time())
            current = session.get('visitedSub', '')
            current_list = [x for x in current.split(',') if x]
            if subtop_param and subtop_param not in current_list:
                current_list.append(subtop_param)
            session['visitedSub'] = ','.join(current_list)
            visited_subtop = current_list

            if lastPage == "c4" and request.method == 'POST':
                ans = request.form.get('ans', '').strip()
                if ans:
                    save_pass_answer('c4', ans, table="tb5_passQop")
                    cursor.execute(
                        """
                        UPDATE tb6_taskTime
                        SET timeEnd=%s, timeEndStamp=%s
                        WHERE uid=%s AND sid=%s AND topID=%s
                        ORDER BY timeStart DESC LIMIT 1
                        """,
                        (
                            int(time.time()),
                            get_time_stamp_cdt(),
                            uid,
                            sid,
                            str(session.get('topID', 1)),
                        ),
                    )
                session.pop('formal_pending_stage', None)
                session.pop('formal_pending_passID', None)
                session.pop('formal_pending_fid', None)
                session.pop('formal_last_page', None)

        # Load subtopics
        cursor.execute("SELECT * FROM tb3_subtopic WHERE topID=%s ORDER BY subtopID", (topID,))
        subtopics = cursor.fetchall()
        all_subtops = [str(row[0]) for row in subtopics]
        all_subtops_sorted = sorted(
            all_subtops,
            key=lambda value: int(value) if str(value).isdigit() else value,
        )
        session['formal_all_subtops'] = all_subtops_sorted

        # If lastPage == c3 and POST, update c3Ans and maybe redirect
        if lastPage == "c3" and request.method == 'POST':
            ans = request.form.get('ans', '')
            passid_to_save = request.form.get('savepassid', '')
            if ans:
                cursor.execute(
                    """
                    UPDATE tb5_passQop SET c3Ans=%s WHERE sid=%s AND uid=%s AND passID=%s
                    """,
                    (ans, sid, uid, passid_to_save),
                )
                # Clear pending formal state after saving c3 answer
                session.pop('formal_pending_stage', None)
                session.pop('formal_pending_passID', None)
                session.pop('formal_pending_fid', None)
                session.pop('formal_last_page', None)

            # Compare visited subtopics with the full set (typed as strings)
            visited_sub = session.get('visitedSub', '')
            visited_list = sorted(
                (x for x in visited_sub.split(',') if x),
                key=lambda value: int(value) if value.isdigit() else value,
            )
            # retain visited list in session
            session['visitedSub'] = ','.join(visited_list)

        link.commit()

        # Load topic
        cursor.execute("SELECT * FROM tb2_topic WHERE topID=%s", (topID,))
        topic_result = cursor.fetchone()

        # save_url
        pageTypeID = "a"
        pageTitle = f"a Task: {topic_result[1]}" if topic_result else "a Task"
        save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

        # define redirect if timer runs out
        session['redirectPage'] = url_for('core.task_b', lastPage='a')

        if not visited_subtop:
            visited_sub = session.get('visitedSub', '')
            visited_subtop = [x for x in visited_sub.split(',') if x]

        visited_sorted = sorted(
            (str(x) for x in visited_subtop if str(x)),
            key=lambda value: int(value) if value.isdigit() else value,
        )
        all_completed = visited_sorted == all_subtops_sorted and bool(all_subtops_sorted)

        return render_template(
            'task_a.html',
            topic_result=topic_result,
            topicResult=topic_result,
            subtopics=subtopics,
            visited_subtop=visited_subtop,
            session=session,
            all_completed=all_completed,
            next_section_url=url_for('core.k2', lastPage='complete'),
        )

    except Exception as e:
        print(f"Error in /task_a route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()


@core_bp.route('/task_b', methods=['GET', 'POST'])
def task_b():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    subtopID = safe_int_param(request.args.get('subtop'), 0)
    conID = safe_int_param(session.get('conID'), 1)
    passOrd = safe_int_param(request.args.get('passOrd'), 1)
    lastPage = request.args.get('lastPage', '')

    try:
        passOrderInt = int(passOrd)
    except ValueError:
        passOrderInt = 1

    passID = format_pass_id(subtopID, conID, passOrd)
    _next_pass_order = passOrderInt + 1

    is_rating_submission = _is_formal_rating_submission()

    redirect_to_next_section = None

    pending_stage = session.get('formal_pending_stage')
    pending_pass = session.get('formal_pending_passID')
    if not is_rating_submission:
        if pending_stage in FORMAL_REQUIRED_STAGES and pending_pass and pending_pass != passID:
            session.pop('formal_pending_stage', None)
            session.pop('formal_pending_passID', None)
            session.pop('formal_pending_fid', None)
            session.pop('formal_last_page', None)
            pending_stage = None
            pending_pass = None
        if pending_stage in FORMAL_REQUIRED_STAGES:
            if pending_stage != 'c1' or pending_pass != passID:
                redirect_url = _formal_pending_redirect()
                if redirect_url:
                    return redirect(redirect_url)

    session['formal_pending_passID'] = passID
    session['formal_pending_stage'] = 'c1'
    session['formal_pending_fid'] = None
    session['formal_last_page'] = lastPage

    session.update({
        'subtopID': subtopID,
        'conID': conID,
        'passOrder': passOrd,
        'passID': passID,
        'next_passOrder': passOrd + 1,
        'nextPassOrder': passOrderInt + 1,
        'topID': session.get('topID', '1'),
    })

    link = None
    cursor = None
    passResult = None
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True, buffered=True)

        cursor.execute(
            """
            SELECT * FROM tb4_passage
            WHERE topID=%s AND subtopID=%s AND conID=%s AND CAST(passOrder AS UNSIGNED)=%s
            """,
            (
                str(session.get('topID', 1)),
                str(subtopID),
                str(conID),
                int(passOrderInt),
            ),
        )
        passResult = cursor.fetchone()
        if passResult and 'passTitle' in passResult:
            session['passTitle'] = passResult['passTitle']

        if passOrd == 1:
            cursor.execute(
                """
                UPDATE tb6_taskTime 
                SET timeStart=%s, timeStartStamp=%s
                WHERE uid=%s AND sid=%s AND topID=%s
                ORDER BY timeStart DESC LIMIT 1
                """,
                (
                    int(time.time()),
                    get_time_stamp_cdt(),
                    uid,
                    sid,
                    session.get('topID', 1),
                ),
            )
            link.commit()

        pageTypeID = "b"
        pageTitle = passResult['passTitle'] if passResult else "No Title"
        save_url(
            uid=uid,
            sid=sid,
            topID=session.get('topID', '1'),
            subtopID=subtopID,
            conID=conID,
            passID=passID,
            pageTypeID=pageTypeID,
            pageTitle=pageTitle,
            url=request.url,
        )

        now = int(time.time())
        if lastPage == "a":
            used_time = now - session.get('lastPageSwitchUnixTime', now)
            session['remainingTime'] = session.get('remainingTime', 0) - used_time
            session['lastPageSwitchUnixTime'] = now
            session['redirectPage'] = url_for('core.task_c1', fid='done')
        elif lastPage == "c3":
            session['lastPageSwitchUnixTime'] = now
            session['redirectPage'] = url_for('core.task_c1', fid='done')
            if request.method == 'POST':
                session.pop('formal_pending_stage', None)
                session.pop('formal_pending_passID', None)
                session.pop('formal_pending_fid', None)
                session.pop('formal_last_page', None)
                ans_to_save = request.form.get('ans', '')
                passid_to_save = request.form.get('savepassid', '')
                if ans_to_save:
                    cursor.execute(
                        """
                        UPDATE tb5_passQop SET c3Ans=%s WHERE sid=%s AND uid=%s AND passID=%s
                        """,
                        (ans_to_save, sid, uid, passid_to_save),
                    )
        elif lastPage == "c4" and request.method == 'POST':
            session.pop('formal_pending_stage', None)
            session.pop('formal_pending_passID', None)
            session.pop('formal_pending_fid', None)
            session.pop('formal_last_page', None)

            current_subtop = str(subtopID)
            visited = [x for x in session.get('visitedSub', '').split(',') if x]
            if current_subtop and current_subtop not in visited:
                visited.append(current_subtop)
            session['visitedSub'] = ','.join(visited)

            visited_sorted = sorted(
                (str(x) for x in visited if str(x)),
                key=lambda value: int(value) if value.isdigit() else value,
            )
            formal_all = session.get('formal_all_subtops') or []
            if formal_all and visited_sorted == formal_all:
                redirect_to_next_section = url_for(
                    'core.task_a',
                    fid='complete',
                    subtop=current_subtop,
                    lastPage='c4',
                    completed='1',
                )

        link.commit()

    except Exception as e:
        print(f"Error in /task_b route: {e}")
        return f"Database error: {e}", 500
    finally:
        if cursor:
            cursor.close()
        if link:
            link.close()

    if redirect_to_next_section:
        return redirect(redirect_to_next_section)

    return render_template('task_b.html', passResult=passResult, passOrder=passOrderInt)


@core_bp.route('/task_c1', methods=['GET', 'POST'])
def task_c1():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    passTitle = session.get('passTitle', '')
    topID = "1"
    conID = "1"
    pageTypeID = "c1"
    pageTitle = f"C1: {passTitle}"

    pending_stage = session.get('formal_pending_stage')
    pending_pass = session.get('formal_pending_passID')
    if pending_stage in FORMAL_REQUIRED_STAGES:
        if pending_pass != passID or pending_stage != 'c1':
            redirect_url = _formal_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)
    else:
        session['formal_pending_passID'] = passID
        session['formal_pending_stage'] = 'c1'

    if fid:
        session['formal_pending_fid'] = fid
    else:
        stored_fid = session.get('formal_pending_fid')
        if stored_fid:
            fid = stored_fid

    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    now = int(time.time())
    last_switch = session.get('lastPageSwitchUnixTime', now)
    session['remainingTime'] = session.get('remainingTime', 0) - (now - last_switch)
    session['lastPageSwitchUnixTime'] = now

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c1")
        if ans:
            save_pass_answer(qid, ans, table="tb5_passQop")
            session['formal_pending_stage'] = 'c2'
            return redirect(url_for('core.task_c2', fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("task_c1.html", fid=fid)


@core_bp.route('/task_c2', methods=['GET', 'POST'])
def task_c2():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    passTitle = session.get('passTitle', '')
    # passOrder kept in session for other routes; not needed locally here
    topID = "1"
    conID = "1"
    pageTypeID = "c2"
    pageTitle = f"C2: {passTitle}"

    pending_stage = session.get('formal_pending_stage')
    pending_pass = session.get('formal_pending_passID')
    if pending_stage in FORMAL_REQUIRED_STAGES:
        if pending_pass != passID or pending_stage != 'c2':
            redirect_url = _formal_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)
    else:
        redirect_url = _formal_pending_redirect()
        if redirect_url:
            return redirect(redirect_url)

    if not fid:
        fid = session.get('formal_pending_fid', 'same')

    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c2")
        if ans:
            save_pass_answer(qid, ans, table="tb5_passQop")
            session['formal_pending_stage'] = 'c3'
            return redirect(url_for('core.task_c3', fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("task_c2.html", fid=fid)


@core_bp.route('/task_c3', methods=['GET', 'POST'])
def task_c3():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    passTitle = session.get('passTitle', '')
    topID = "1"
    conID = "1"
    # nextPassOrder not used in this scope; keep session value usage elsewhere
    # and avoid an unused local variable warning
    _next_pass_order = session.get('nextPassOrder', 2)

    pageTypeID = "c3"
    pageTitle = f"C3: {passTitle}"

    pending_stage = session.get('formal_pending_stage')
    pending_pass = session.get('formal_pending_passID')
    if pending_stage in FORMAL_REQUIRED_STAGES:
        if pending_pass != passID or pending_stage != 'c3':
            redirect_url = _formal_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)
    else:
        redirect_url = _formal_pending_redirect()
        if redirect_url:
            return redirect(redirect_url)

    if not fid:
        fid = session.get('formal_pending_fid', 'same')

    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c3")
        if ans:
            save_pass_answer(qid, ans, table="tb5_passQop")
            session['formal_pending_stage'] = 'c4'
            return redirect(url_for('core.task_c4', fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("task_c3.html", fid=fid, passID=passID)


@core_bp.route('/task_c4', methods=['GET', 'POST'])
def task_c4():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    passID = session.get('passID', '')

    pending_stage = session.get('formal_pending_stage')
    pending_pass = session.get('formal_pending_passID')
    if pending_stage in FORMAL_REQUIRED_STAGES:
        if pending_pass != passID or pending_stage != 'c4':
            redirect_url = _formal_pending_redirect()
            if redirect_url:
                return redirect(redirect_url)
    else:
        redirect_url = _formal_pending_redirect()
        if redirect_url:
            return redirect(redirect_url)

    if not fid:
        fid = session.get('formal_pending_fid', 'same')

    if fid == "same":
        action_url = url_for('core.task_b', subtop=session.get('subtopID', ''), passOrd=session.get('nextPassOrder', 1), lastPage='c4')
    elif fid == "back":
        action_url = url_for('core.task_a', fid='back', subtop=session.get('subtopID', ''), lastPage='c4')
    elif fid == "done":
        action_url = url_for('core.k2', lastPage='c4')
    else:
        action_url = url_for('core.k2', lastPage='unknown')

    _subtopID = session.get('subtopID', '')
    _passID = session.get('passID', '')
    pageTypeID = "c4"
    passTitle = session.get('passTitle', '')
    pageTitle = f"C4: {passTitle}"
    save_url(uid, sid, "", "", "", "", pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c4")
        if ans:
            save_pass_answer(qid, ans, table="tb5_passQop")
            try:
                link = get_db_connection()
                cursor = link.cursor()
                cursor.execute(
                    """
                    UPDATE tb6_taskTime
                    SET timeEnd=%s, timeEndStamp=%s
                    WHERE uid=%s AND sid=%s AND topID=%s
                    ORDER BY timeStart DESC LIMIT 1
                    """,
                    (
                        int(time.time()),
                        get_time_stamp_cdt(),
                        uid,
                        sid,
                        str(session.get('topID', 1)),
                    ),
                )
                link.commit()
            except Exception as e:
                print(f"DB error in task_c4 POST: {e}")
                return f"Database error: {e}", 500
            finally:
                if link and link.is_connected():
                    cursor.close()
                    link.close()
            session.pop('formal_pending_stage', None)
            session.pop('formal_pending_passID', None)
            session.pop('formal_pending_fid', None)
            session.pop('formal_last_page', None)
            return redirect(action_url)
        else:
            return "No answer provided.", 400

    return render_template("task_c4.html", fid=fid, action_url=action_url)


@core_bp.route('/let_comp_one_inst', methods=['GET', 'POST'])
def let_comp_one_inst():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    topID = "1"
    pageTypeID = "inst_lci1"
    pageTitle = "Instruction for Letter Comparison One"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans_to_save = request.form.get("textarea_k2", "").strip()
        try:
            link = get_db_connection()
            cursor = link.cursor()
            cursor.execute(
                """
                INSERT INTO tb8_topicIdeas (uid, sid, topID, quesID, quesAns)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (uid, sid, topID, "k2", ans_to_save),
            )
            link.commit()
        except Exception as e:
            print(f"Error inserting topic idea: {e}")
            return f"Database error: {e}", 500
        finally:
            if link and link.is_connected():
                cursor.close()
                link.close()

    return render_template("let_comp_one_inst.html")


def _letter_round_items(round_number: int):
    return LETTER_COMPARISON_ROUNDS.get(round_number, [])


def _letter_round_column(round_number: int, item_index: int) -> str:
    base_offset = 0 if round_number == 1 else 10
    return f"lc{base_offset + item_index}"


def _letter_round_pass_id(round_number: int, item_index: int) -> str:
    return f"LC{round_number}{item_index:02d}"


def _save_letter_item_response(
    uid: int,
    sid: str,
    round_number: int,
    item_index: int,
    item: dict,
    response: str,
    is_correct: int,
):
    """Persist per-item letter comparison response and timestamp metadata."""
    link = None
    cursor = None
    try:
        link = get_db_connection()
        cursor = link.cursor()

        cursor.execute(
            """
            INSERT INTO tb27_letter_item
                (uid, sid, round_number, item_index, left_str, right_str, correct_answer,
                 response, is_correct)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                response = VALUES(response),
                is_correct = VALUES(is_correct),
                updated_at = CURRENT_TIMESTAMP(6)
            """,
            (
                uid,
                sid,
                round_number,
                item_index,
                item["left"],
                item["right"],
                item["answer"],
                response,
                is_correct,
            ),
        )

        column_name = _letter_round_column(round_number, item_index)
        cursor.execute(
            f"UPDATE tb11_profile SET {column_name}=%s WHERE sid=%s AND uid=%s",
            (response, sid, uid),
        )

        link.commit()
    except Exception as e:
        print(f"Error saving letter comparison response: {e}")
        if link:
            link.rollback()
    finally:
        if cursor:
            cursor.close()
        if link and link.is_connected():
            link.close()


def _finalize_letter_round_with_total_time(uid: int, sid: str, round_number: int, total_rt_sec: int) -> None:
    """Save total time (seconds) for letter comparison round without individual item times."""
    link = None
    cursor = None
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True, buffered=True)
        
        # 计算正确题目数量
        cursor.execute(
            """
            SELECT COALESCE(SUM(is_correct), 0) AS correct_count
            FROM tb27_letter_item
            WHERE uid=%s AND sid=%s AND round_number=%s
            """,
            (uid, sid, round_number),
        )
        row = cursor.fetchone() or {"correct_count": 0}
        
        # 根据轮次设置字段名
        score_col = "lcOneScore" if round_number == 1 else "lcTwoScore"
        rt_col = "lcOneRT" if round_number == 1 else "lcTwoRT"
        
        # 更新到tb11_profile表
        cursor.execute(
            f"UPDATE tb11_profile SET {score_col}=%s, {rt_col}=%s WHERE sid=%s AND uid=%s",
            (row["correct_count"], total_rt_sec, sid, uid),
        )
        link.commit()
    except Exception as e:
        print(f"Error finalizing letter comparison round {round_number}: {e}")
        if link:
            link.rollback()
    finally:
        if cursor:
            cursor.close()
        if link:
            link.close()


def _finalize_letter_round(uid: int, sid: str, round_number: int) -> None:
    """Aggregate per-round accuracy and RT totals into tb11_profile."""
    link = None
    cursor = None
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True, buffered=True)
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(is_correct), 0) AS correct_count,
                COALESCE(
                    TIMESTAMPDIFF(
                        SECOND,
                        MIN(created_at),
                        MAX(updated_at)
                    ),
                    0
                ) AS span_seconds
            FROM tb27_letter_item
            WHERE uid=%s AND sid=%s AND round_number=%s
            """,
            (uid, sid, round_number),
        )
        row = cursor.fetchone() or {"correct_count": 0, "span_seconds": 0}
        score_col = "lcOneScore" if round_number == 1 else "lcTwoScore"
        rt_col = "lcOneRT" if round_number == 1 else "lcTwoRT"
        total_rt_sec = int(row.get("span_seconds") or 0)
        cursor.execute(
            f"UPDATE tb11_profile SET {score_col}=%s, {rt_col}=%s WHERE sid=%s AND uid=%s",
            (row["correct_count"], total_rt_sec, sid, uid),
        )
        link.commit()
    except Exception as e:
        print(f"Error finalizing letter comparison round {round_number}: {e}")
        if link:
            link.rollback()
    finally:
        if cursor:
            cursor.close()
        if link:
            link.close()


@core_bp.route('/let_comp_one', methods=['GET', 'POST'])
def let_comp_one():
    return _handle_letter_round_all(round_number=1, completion_endpoint='core.let_comp_two_inst')


@core_bp.route('/let_comp_two_inst', methods=['GET', 'POST'])
def let_comp_two_inst():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    topID = "1"
    pageTypeID = "inst_lc2"
    pageTitle = "Instruction for Letter Comparison Two"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    return render_template("let_comp_two_inst.html")


@core_bp.route('/let_comp_two', methods=['GET', 'POST'])
def let_comp_two():
    return _handle_letter_round_all(round_number=2, completion_endpoint='core.vocab')


def _handle_letter_round_all(round_number: int, completion_endpoint: str):
    """Handle letter comparison round with all items displayed on one page."""
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    items = _letter_round_items(round_number)
    total_items = len(items)
    if total_items == 0:
        print(f"No letter comparison items configured for round {round_number}")
        return redirect(url_for(completion_endpoint))

    if request.method == 'POST':
        if request.form.get('save_only') == '1':
            item_index = safe_int_param(request.form.get('item_index'), 1)
            if item_index < 1 or item_index > total_items:
                return "Invalid item index.", 400
            choice = request.form.get('choice', '').strip().upper()
            if choice not in {'S', 'D'}:
                return "Invalid response.", 400
            item = items[item_index - 1]
            is_correct = 1 if choice == item['answer'] else 0
            _save_letter_item_response(uid, sid, round_number, item_index, item, choice, is_correct)
            return ("", 204)

        # 从前端获取总时间（从页面加载到点击done）
        total_time_ms = request.form.get('total_time_ms')
        if not total_time_ms:
            return "Missing total time data.", 400

        try:
            total_rt_ms = int(total_time_ms)
        except (ValueError, TypeError):
            return "Invalid total time data.", 400

        total_rt_sec = int(round(total_rt_ms / 1000.0))

        skip_save = request.form.get('skip_save') == '1'
        if not skip_save:
            responses = []
            for i, item in enumerate(items, 1):
                choice_key = f'choice_{i}'
                choice = request.form.get(choice_key, '').strip().upper()
                if choice not in {'S', 'D'}:
                    return f"Invalid response for item {i}.", 400
                is_correct = 1 if choice == item['answer'] else 0
                responses.append({
                    'item_index': i,
                    'item': item,
                    'choice': choice,
                    'is_correct': is_correct
                })

            for response in responses:
                _save_letter_item_response(
                    uid,
                    sid,
                    round_number,
                    response['item_index'],
                    response['item'],
                    response['choice'],
                    response['is_correct'],
                )

        _finalize_letter_round_with_total_time(uid, sid, round_number, total_rt_sec)
        return redirect(url_for(completion_endpoint))

    # GET请求 - 显示所有题目
    top_id = session.get('topID', '1')
    page_type = f'start_lc{round_number}_all'
    page_title = f"Letter Comparison {round_number} - All Items"
    pass_id = f"LC{round_number}00"  # 使用特殊ID表示所有题目
    
    save_url(
        uid, sid, top_id, '', '', pass_id, page_type, page_title, request.url
    )

    action_url = url_for(request.endpoint)
    return render_template(
        'letter_comp_all.html',
        round_number=round_number,
        items=items,
        total_items=total_items,
        action_url=action_url,
    )


def _handle_letter_round(round_number: int, completion_endpoint: str):
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    items = _letter_round_items(round_number)
    total_items = len(items)
    if total_items == 0:
        print(f"No letter comparison items configured for round {round_number}")
        return redirect(url_for(completion_endpoint))

    if request.method == 'POST':
        item_index = safe_int_param(request.form.get('item_index'), 1)
        if item_index < 1 or item_index > total_items:
            return redirect(url_for(completion_endpoint))

        choice = request.form.get('choice', '').strip().upper()
        if choice not in {'S', 'D'}:
            return "Invalid response.", 400

        item = items[item_index - 1]
        is_correct = 1 if choice == item['answer'] else 0

        if request.form.get('save_only') == '1':
            _save_letter_item_response(uid, sid, round_number, item_index, item, choice, is_correct)
            return ("", 204)

        skip_save = request.form.get('skip_save') == '1'
        if not skip_save:
            _save_letter_item_response(uid, sid, round_number, item_index, item, choice, is_correct)

        next_index = item_index + 1
        if next_index <= total_items:
            return redirect(url_for(request.endpoint, item=next_index))

        _finalize_letter_round(uid, sid, round_number)
        return redirect(url_for(completion_endpoint))

    item_index = safe_int_param(request.args.get('item'), 1)
    if item_index < 1 or item_index > total_items:
        return redirect(url_for(completion_endpoint))

    item = items[item_index - 1]
    top_id = session.get('topID', '1')
    pass_id = _letter_round_pass_id(round_number, item_index)
    if item_index == 1:
        page_type = 'start_lc1' if round_number == 1 else 'start_lc2'
    else:
        page_type = f'lc{round_number}_item'
    page_title = f"Letter Comparison {round_number} - Item {item_index}"
    save_url(
        uid,
        sid,
        top_id,
        '',
        '',
        pass_id,
        page_type,
        page_title,
        request.url,
    )

    action_url = url_for(request.endpoint)
    is_last = item_index == total_items
    return render_template(
        'letter_comp_item.html',
        round_number=round_number,
        item_index=item_index,
        total_items=total_items,
        left_string=item['left'],
        right_string=item['right'],
        action_url=action_url,
        is_last=is_last,
    )


@core_bp.route('/k2', methods=['GET', 'POST'])
def k2():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    is_rating_submission = _is_formal_rating_submission()

    if not is_rating_submission:
        pending_redirect = _formal_pending_redirect()
        if pending_redirect:
            return redirect(pending_redirect)

    topID = "1"
    link = None
    cursor = None
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM tb2_topic WHERE topID = %s", (topID,))
        topic_row = cursor.fetchone()
        topicTitle = topic_row['topTitle'] if topic_row else "Unknown Topic"
        subtop_list = []
        cursor.execute("SELECT * FROM tb3_subtopic WHERE topID = %s ORDER BY subtopID", (topID,))
        subtop_rows = cursor.fetchall()
        for row in subtop_rows:
            subtop_list.append(row['subtopTitle'])
    except Exception as e:
        print(f"Error retrieving topic/subtopics: {e}")
        return f"Database error: {e}", 500
    finally:
        if cursor:
            cursor.close()
        if link:
            link.close()

    subtopString = ", ".join(subtop_list)
    trimSubtop = subtopString.lstrip(", ").strip()
    lastPage = request.args.get('lastPage', '')

    if lastPage == 'complete':
        link = None
        cursor = None
        try:
            link = get_db_connection()
            cursor = link.cursor()
            cursor.execute(
                "UPDATE tb1_user SET conDone = conDone + 1 WHERE sid = %s AND uid = %s",
                (sid, uid),
            )
            link.commit()
        except Exception as e:
            if link:
                link.rollback()
            print(f"Error updating conDone in /k2 complete redirect: {e}")
            return f"Database error: {e}", 500
        finally:
            if cursor:
                cursor.close()
            if link and link.is_connected():
                link.close()
        session.pop('formal_pending_stage', None)
        session.pop('formal_pending_passID', None)
        session.pop('formal_pending_fid', None)
        session.pop('formal_last_page', None)
        session['redirectPage'] = url_for('core.let_comp_one_inst')
        return redirect(url_for('core.k2'))

    if lastPage == "c4" and request.method == "POST":
        ans_to_save = request.form.get('ans', '').strip()
        passid_to_save = request.form.get('savepassid', '')
        if ans_to_save:
            try:
                link = get_db_connection()
                cursor = link.cursor()
                cursor.execute(
                    """
                    UPDATE tb5_passQop 
                    SET c3Ans = %s 
                    WHERE sid = %s AND uid = %s AND passID = %s
                    """,
                    (ans_to_save, sid, uid, passid_to_save),
                )
                cursor.execute("UPDATE tb1_user SET conDone = conDone + 1 WHERE sid = %s AND uid = %s", (sid, uid))
                link.commit()
            except Exception as e:
                print(f"Error updating c3Ans in /k2: {e}")
                return f"Database error: {e}", 500
            finally:
                if link and link.is_connected():
                    cursor.close()
                    link.close()
            session.pop('formal_pending_stage', None)
            session.pop('formal_pending_passID', None)
            session.pop('formal_pending_fid', None)
            session.pop('formal_last_page', None)

    pageTypeID = "k2"
    pageTitle_full = f"K2: {topicTitle}"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle_full, request.url)
    session['redirectPage'] = url_for('core.let_comp_one_inst')
    action_url = url_for('core.let_comp_one_inst')
    return render_template("k2.html", topicTitle=topicTitle, trimSubtop=trimSubtop, action_url=action_url)


@core_bp.route('/vocab', methods=['GET'])
def vocab():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return redirect(url_for('core.index'))
    # Log entering vocab
    save_url(uid, sid, "1", "", "", "", "vocab", "Vocabulary", request.url)
    return render_template('vocab.html', action_url=url_for('core.questions'))


@core_bp.route('/questions', methods=['GET', 'POST'])
def questions():
    uid = session.get('uid')
    sid = session.get('sid', '')
    passID = session.get('passID', '')
    if not uid:
        return redirect(url_for('core.index'))

    topID = "1"
    pageTypeID = "DONE"
    pageTitle = "DONE"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    if request.method == "POST" and request.form.get("voc1", "").strip() != "":
        voc = [request.form.get(f"voc{i}", "").strip() for i in range(1, 16)]
        right = ["1", "2", "2", "2", "3", "2", "4", "1", "4", "5", "3", "4", "1", "3", "5"]
        numCorrect = 0
        numWrong = 0
        numNotSure = 0
        for i in range(15):
            if voc[i] == right[i]:
                numCorrect += 1
            else:
                if voc[i] == "6":
                    numNotSure += 1
                else:
                    numWrong += 1
        vocScore = (1 * numCorrect) - (0.2 * numWrong)
        try:
            link = get_db_connection()
            cursor = link.cursor()
            cursor.execute(
                """
                UPDATE tb11_profile
                SET voc1=%s, voc2=%s, voc3=%s, voc4=%s, voc5=%s,
                    voc6=%s, voc7=%s, voc8=%s, voc9=%s, voc10=%s,
                    voc11=%s, voc12=%s, voc13=%s, voc14=%s, voc15=%s,
                    vocScore=%s
                WHERE sid=%s AND uid=%s
                """,
                (*voc, vocScore, sid, uid),
            )
            link.commit()
        except Exception as e:
            print(f"Error updating vocabulary answers: {e}")
            return f"Database error: {e}", 500
        finally:
            if link and link.is_connected():
                cursor.close()
                link.close()

    questions_by_passage = []
    existing_answers = {}
    pass_ids = []

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        q_top = str(session.get('topID', '1'))
        q_sub = session.get('subtopID')
        q_con = session.get('conID')
        q_ord = session.get('passOrder')

        cursor.execute(
            """
            SELECT passID, subtopID, passOrder
            FROM tb5_passQop
            WHERE uid=%s AND sid=%s AND topID=%s
            GROUP BY passID, subtopID, passOrder
            ORDER BY CAST(subtopID AS UNSIGNED), CAST(passOrder AS UNSIGNED)
            """,
            (uid, sid, q_top),
        )
        pass_rows = cursor.fetchall()
        pass_ids = [row['passID'] for row in pass_rows if row.get('passID')]

        if not pass_ids:
            if passID:
                pass_ids = [passID]
            elif q_sub is not None and q_con is not None and q_ord is not None:
                try:
                    pass_ids = [format_pass_id(int(q_sub), int(q_con), int(q_ord))]
                except (TypeError, ValueError):
                    pass_ids = []

        if pass_ids:
            placeholders = ','.join(['%s'] * len(pass_ids))
            cursor.execute(
                f"""
                SELECT * FROM tb21_questions
                WHERE passID IN ({placeholders})
                ORDER BY passID, questionID
                """,
                tuple(pass_ids),
            )
            question_rows = cursor.fetchall()

            questions_by_passage = []
            current_block = None
            for row in question_rows:
                pass_key = row.get('passID')
                if not current_block or current_block['passID'] != pass_key:
                    current_block = {
                        'passID': pass_key,
                        'passTitle': row.get('passTitle') or pass_key,
                        'questions': [],
                    }
                    questions_by_passage.append(current_block)
                current_block['questions'].append(row)

            cursor.execute(
                f"""
                SELECT questionID, choice 
                FROM tb22_multiQop 
                WHERE uid = %s AND sid = %s AND passID IN ({placeholders})
                """,
                (uid, sid, *pass_ids),
            )
            existing_answers = {row['questionID']: row['choice'] for row in cursor.fetchall()}
        else:
            questions_by_passage = []
            existing_answers = {}
    except Exception as e:
        print(f"Database error preparing comprehension questions: {str(e)}")
        questions_by_passage = []
        existing_answers = {}
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return render_template(
        'questions.html',
        questions_by_passage=questions_by_passage,
        existing_answers=existing_answers,
    )


@core_bp.route('/done', methods=['GET', 'POST'])
def done():
    uid = session.get('uid')
    sid = session.get('sid', '')
    passID = session.get('passID', '')
    if not uid:
        return redirect(url_for('core.index'))

    bonusWordsCnt = 0
    topID = "1"

    pass_ids = []
    pass_conn = None
    pass_cursor = None
    try:
        pass_conn = get_db_connection()
        pass_cursor = pass_conn.cursor(dictionary=True)
        pass_cursor.execute(
            """
            SELECT passID, subtopID, passOrder
            FROM tb5_passQop
            WHERE uid=%s AND sid=%s AND topID=%s
            GROUP BY passID, subtopID, passOrder
            ORDER BY CAST(subtopID AS UNSIGNED), CAST(passOrder AS UNSIGNED)
            """,
            (uid, sid, topID),
        )
        for row in pass_cursor.fetchall():
            pid = row.get('passID')
            if pid:
                pass_ids.append(pid)
    except Exception as e:
        print(f"Database error gathering comprehension pass IDs: {str(e)}")
    finally:
        if pass_cursor:
            pass_cursor.close()
        if pass_conn and pass_conn.is_connected():
            pass_conn.close()

    if not pass_ids and passID:
        pass_ids = [passID]

    if request.method == 'POST' and pass_ids:
        submit_conn = None
        submit_cursor = None
        try:
            submit_conn = get_db_connection()
            submit_cursor = submit_conn.cursor(dictionary=True)
            placeholders = ','.join(['%s'] * len(pass_ids))
            submit_cursor.execute(
                f"""
                SELECT * FROM tb21_questions
                WHERE passID IN ({placeholders})
                ORDER BY passID, questionID
                """,
                tuple(pass_ids),
            )
            questions = submit_cursor.fetchall()
            for q in questions:
                field_name = f"q_{q['questionID']}"
                user_choice = request.form.get(field_name, '').lower()
                if not user_choice:
                    continue
                is_correct = 1 if user_choice == q['correctAns'].lower() else 0
                submit_cursor.execute(
                    """
                    INSERT INTO tb22_multiQop (
                        uid, sid, questionID, topID, subtopID,
                        conID, passID, passOrder, choice, isCorrect
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        choice = VALUES(choice),
                        isCorrect = VALUES(isCorrect)
                    """,
                    (
                        uid,
                        sid,
                        q['questionID'],
                        q['topID'],
                        q['subtopID'],
                        q['conID'],
                        q['passID'],
                        q['passOrder'],
                        user_choice,
                        is_correct,
                    ),
                )
            submit_conn.commit()
        except Exception as e:
            print(f"Database error processing answers: {str(e)}")
            if submit_conn:
                submit_conn.rollback()
        finally:
            if submit_cursor:
                submit_cursor.close()
            if submit_conn and submit_conn.is_connected():
                submit_conn.close()

    # Update time intervals in output1_url, update RTs, bonuses, etc. Kept same as original for brevity.
    link = None
    cursor = None
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True, buffered=True)
        cursor.execute(
            """
            SELECT * FROM output1_url
            WHERE sid=%s AND uid=%s
            ORDER BY op1ID DESC
            """,
            (sid, uid),
        )
        op_results = cursor.fetchall()
        nextUnixTime = 0
        for row in op_results:
            rowID = row.get('op1ID', 0)
            if rowID > 0:
                thisUnixTime = row.get('unixTime', 0)
                timeInterval = abs(nextUnixTime - thisUnixTime) if nextUnixTime else 0
                if row.get('pageTypeID') != "DONE":
                    cursor.execute("UPDATE output1_url SET time_interval=%s WHERE op1ID=%s", (timeInterval, rowID))
                nextUnixTime = thisUnixTime
        link.commit()
    except Exception as e:
        print(f"Error updating time intervals: {e}")
    finally:
        if cursor:
            cursor.close()
        if link:
            link.close()

    # passage RT for formal reading pages (pageTypeID='b')
    link = None
    cursor = None
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT passID, time_interval FROM output1_url WHERE sid=%s AND uid=%s AND pageTypeID='b'", (sid, uid))
        for row in cursor.fetchall():
            qryPassID = row['passID']
            qryPassRT = row['time_interval']
            cursor.execute(
                "UPDATE tb5_passQop SET passRT=%s WHERE sid=%s AND uid=%s AND passID=%s",
                (qryPassRT, sid, uid, qryPassID),
            )
        link.commit()
    except Exception as e:
        print(f"Error updating passage reading time for b: {e}")
    finally:
        if cursor:
            cursor.close()
        if link:
            link.close()

    # passage RT for practice reading pages (pageTypeID='prac_b')
    link = None
    cursor = None
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT passID, time_interval FROM output1_url WHERE sid=%s AND uid=%s AND pageTypeID='prac_b'", (sid, uid))
        for row in cursor.fetchall():
            qryPassID = row['passID']
            qryPassRT = row['time_interval']
            cursor.execute(
                "UPDATE tb15_prac_passQop SET passRT=%s WHERE sid=%s AND uid=%s AND passID=%s",
                (qryPassRT, sid, uid, qryPassID),
            )
        link.commit()
    except Exception as e:
        print(f"Error updating passage reading time for prac_b: {e}")
    finally:
        if cursor:
            cursor.close()
        if link:
            link.close()

    # Sync letter comparison aggregates from per-item records
    _finalize_letter_round(uid, sid, 1)
    _finalize_letter_round(uid, sid, 2)

    # Compute comprehension accuracy percentage as bonusWordsCnt (0-100)
    link = None
    cursor = None
    bonusWordsCnt = 0
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True, buffered=True)
        '''
        cursor.execute("SELECT * FROM tb2_topic WHERE topID=%s", (topID,))
        topicRow = cursor.fetchone()
        topicIdeasBWsString = topicRow.get('topIdeasBonusWords', "") if topicRow else ""
        topicIdeasBWsArray = topicIdeasBWsString.split(" ") if topicIdeasBWsString else []
        cursor.execute("SELECT * FROM tb8_topicIdeas WHERE topID=%s AND sid=%s AND uid=%s", (topID, sid, uid))
        topicIdeasAnsRow = cursor.fetchone()
        topicIdeasAnsString = topicIdeasAnsRow.get('quesAns', "") if topicIdeasAnsRow else ""
        topicIdeasAnsStringAry = []
        for line in topicIdeasAnsString.split("\n"):
            for word in line.split(" "):
                cleaned = word.strip()
                if cleaned:
                    import re
                    cleaned = re.sub(r"[^0-9a-zA-Z]+", "", cleaned)
                    topicIdeasAnsStringAry.append(cleaned.lower())
        bonusWordsAry = []
        for word in topicIdeasAnsStringAry:
            if word and word in topicIdeasBWsArray:
                bonusWordsAry.append(word)
                bonusWordsCnt += 1
        bonusWordsMoney = 0.05 * bonusWordsCnt
        bonusWordsString = " ".join(bonusWordsAry)
        cursor.execute(
            """
            INSERT INTO tb9_topicBonus 
                (uid, sid, topID, quesID, quesAns, bonusWord, bonusWordCnt, bonusMoney)
            VALUES (%s, %s, %s, 'k2', %s, %s, %s, %s)
            """,
            (uid, sid, topID, topicIdeasAnsString, bonusWordsString, bonusWordsCnt, bonusWordsMoney),
        )
        link.commit()
        print(f"Error processing bonus words: {e}")
        '''

        if pass_ids:
            placeholders = ','.join(['%s'] * len(pass_ids))
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total, COALESCE(SUM(isCorrect), 0) AS correct
                FROM tb22_multiQop
                WHERE uid=%s AND sid=%s AND passID IN ({placeholders})
                """,
                (uid, sid, *pass_ids),
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS total, COALESCE(SUM(isCorrect), 0) AS correct
                FROM tb22_multiQop
                WHERE uid=%s AND sid=%s
                """,
                (uid, sid),
            )

        row = cursor.fetchone() or {"total": 0, "correct": 0}
        total = int(row.get("total") or 0)
        correct = int(row.get("correct") or 0)
        bonusWordsCnt = int(round((correct / total) * 100)) if total > 0 else 0
    except Exception as e:
        '''print(f"Error processing bonus words: {e}")'''
        print(f"Error computing comprehension accuracy: {e}")
        bonusWordsCnt = 0
    finally:
        if cursor:
            cursor.close()
        if link:
            link.close()

    try:
        mTurkUniCode = 999 - int(uid)
    except Exception:
        mTurkUniCode = 0
    final_code = f"9XQE783CE{mTurkUniCode}"
    return render_template("done.html", bonusWordsCnt=bonusWordsCnt, final_code=final_code)
