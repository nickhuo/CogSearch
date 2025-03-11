from flask import Flask, render_template, session, request, redirect, url_for, g, session, jsonify
import sqlite3
import time
import os
from datetime import datetime
import click
# Add to existing imports
from werkzeug.exceptions import BadRequestKeyError
import mysql.connector
from mysql.connector import Error
from db_utils import get_db_connection, get_time_stamp_cdt, save_url

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
# app.config['DATABASE'] = os.path.join(app.instance_path, 'app.db')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'cogsearch_textsearch3'

@app.route('/save_url', methods=['POST'])
def handle_save_url():
    """
    Example route that uses the save_url function.
    We assume the POST data contains the same parameters 
    you'd normally get from $_POST or $_SESSION in PHP.
    """
    # In PHP, you used $_SESSION['uid'], so let's assume you store it in Flask's session
    uid = session.get('uid')
    
    # The rest might come from request.form or session, depending on your logic
    sid         = request.form.get('sid', '')
    topID       = request.form.get('topID', '')
    subtopID    = request.form.get('subtopID', '')
    conID       = request.form.get('conID', '')
    passID      = request.form.get('passID', '')
    pageTypeID  = request.form.get('pageTypeID', '')
    timeStamp   = request.form.get('timeStamp', '')
    unixTime    = request.form.get('unixTime', 0)   # or cast to int if needed
    url_str     = request.form.get('url', '')
    pageTitle   = request.form.get('pageTitle', '')

    success = save_url(
        uid,
        sid,
        topID,
        subtopID,
        conID,
        passID,
        pageTypeID,
        timeStamp,
        int(unixTime),
        url_str,
        pageTitle
    )

    if success:
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error'}), 500

@app.route('/task_setting')
def task_setting():
    topID = request.args.get('topID', 'unknown')
    return render_template('task_setting.html', topID=topID)

@app.route('/settings')
def settings():
    uid = session.get('uid')
    if not uid:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT topIDorder, taskDone FROM tb1_user WHERE uid = %s", (uid,))
    user_data = cur.fetchone()
    cur.close()
    
    if not user_data:
        return "User data not found", 404
    
    topIDorder, taskDone = user_data['topIDorder'], user_data['taskDone']
    task_array = list_order(topIDorder, 1) if topIDorder else []
    
    current_topID = task_array[taskDone] if (taskDone >= 0 and taskDone < len(task_array)) else ""
    
    return render_template('settings.html', 
                           current_topID=current_topID,
                           user_id=uid,
                           session_id=session.get('sid'))

def list_order(input_string, number):
    """
    Example: 
      input_string = "T1#T2#T3#"
      number = 3
    Returns ["T1", "T2", "T3"]
    """
    tasks = []
    for _ in range(number):
        # find position of first '#'
        cur_pos = input_string.find('#')
        # substring up to '#'
        tasks.append(input_string[:cur_pos])
        # remove that segment plus the '#' from the input_string
        input_string = input_string[cur_pos+1:]
    return tasks

# A route that acts like done.php?sid=xxx
@app.route('/done')
def done_route():
    sid = request.args.get('sid', '')
    return f"<h1>All tasks are done. sid={sid}</h1>"

@app.route('/timer')
def timer_page():
    # If you want to ensure the user is logged in, do a check:
    # if 'uid' not in session or 'sid' not in session:
    #     return redirect(url_for('consent_route'))

    # Retrieve from session what PHP used to get from $_SESSION
    remaining_time = session.get('remainingTime', 0)
    redirect_page = session.get('redirectPage', '')

    # Render the timer template, passing those two values
    return render_template(
        'timer.html',
        remaining_time=remaining_time,
        redirect_page=redirect_page
    )

def get_time_stamp_cdt():
    """
    Equivalent to gmdate("Y-m-d H:i:s", time()-3600*5) in PHP
    """
    # Subtract 5 hours from UTC
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() - 3600*5))

# Example route to set up session['remainingTime'] and session['redirectPage']
# (just a demo; in your real code, you'd set this after a user does something)
@app.route('/set_timer')
def set_timer():
    session['remainingTime'] = 30000  # 300 seconds = 5 minutes
    session['redirectPage'] = '/done'  # e.g. redirect to a "done" page
    return redirect(url_for('timer_page'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/warning')
def warning():
    return render_template('warning.html')

@app.route('/consent', methods=['GET'])
def consent():
    if 'sid' in session:
        session.clear()
    return render_template('consent.html')


# ----------------------------------------------------
#  DEMOGRAPHIC
# ----------------------------------------------------
@app.route('/demographic', methods=['POST'])
def demographic():
    # If a uid already exists, clear it
    if 'uid' in session and session['uid']:
        session['uid'] = ""

    # Use mTurk Worker ID as sid from the form field (assumed to be named "mturkid")
    sid = request.form.get('mturkid', '').strip()
    session['sid'] = sid

    link = None
    try:
        link = get_db_connection()
        cursor = link.cursor()

        timeStamp = get_time_stamp_cdt()

        # Insert a new row into tb1_user.
        # We explicitly set topIDorder, subtopIDorder, conIDorder to empty strings.
        insert_user = """
            INSERT INTO tb1_user 
                (sid, topIDorder, subtopIDorder, conIDorder, taskDone, conDone, signedConsent, signedDate)
            VALUES
                (%s, '', '', '', 0, 0, 'TRUE', %s)
        """
        cursor.execute(insert_user, (sid, timeStamp))

        # Retrieve the newly assigned uid and store in session
        cursor.execute("SELECT MAX(uid) FROM tb1_user WHERE sid=%s", (sid,))
        row = cursor.fetchone()
        if row and row[0]:
            session['uid'] = row[0]

        # Now, check if demographic answer fields exist.
        # The original saveDemog.php expects:
        #   bmv, bdv, byv, agev, genv, eduv, natengv, firlanv, ageengv, hislatv, racev
        # Our HTML form uses names: demog_bm, demog_bd, demog_by, demog_age, demog_gen, demog_edu, demog_eng, demog_firlan, demog_ageeng, demog_hislat, demog_race.
        bmv = request.form.get("demog_bm", "").strip()
        if bmv:
            bdv = request.form.get("demog_bd", "").strip()
            byv = request.form.get("demog_by", "").strip()
            # Combine into a "dob summary"
            bsv = f"{bmv}/{bdv}/{byv}"
            agev = request.form.get("demog_age", "").strip()
            genv = request.form.get("demog_gen", "").strip()
            eduv = request.form.get("demog_edu", "").strip()
            natengv = request.form.get("demog_eng", "").strip()
            firlanv = request.form.get("demog_firlan", "").strip()
            ageengv = request.form.get("demog_ageeng", "").strip()
            hislatv = request.form.get("demog_hislat", "").strip()
            racev = request.form.get("demog_race", "").strip()

            insert_demo = """
                INSERT INTO tb11_profile
                    (uid, sid, dobMonth, dobDay, dobYear, dobSum, age, gender, edu, natEng, firLan, ageEng, hisLat, race)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_demo, (
                session['uid'], sid,
                bmv, bdv, byv, bsv,
                agev, genv, eduv, natengv, firlanv, ageengv, hislatv, racev
            ))

        # Log the page visit using save_url with pageTypeID "start_demog"
        action = url_for('prac_instruction')  # Next step route
        pageTypeID = "start_demog"
        pageTitle = "Start Demographic Information"
        save_url(session['uid'], sid, "", "", "", "", pageTypeID, pageTitle, request.url)

        link.commit()

    except Exception as e:
        print(f"DB Error in /demographic: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template('demographic.html')



# ----------------------------------------------------
#  PRAC_INSTRUCTION
# ----------------------------------------------------
@app.route('/prac_instruction', methods=['POST'])
def prac_instruction():
    """
    Inserts demographic answers into tb11_profile if posted, 
    then displays the instructions page.
    """
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    link = None
    try:
        link = get_db_connection()
        cursor = link.cursor()

        # Possibly store demographic answers
        bmv = request.form.get('demog_bm')
        if bmv:
            bdv     = request.form.get('demog_bd', '')
            byv     = request.form.get('demog_by', '')
            bsv     = f"{bmv}/{bdv}/{byv}"
            agev    = request.form.get('demog_age', '')
            genv    = request.form.get('demog_gen', '')
            eduv    = request.form.get('demog_edu', '')
            natengv = request.form.get('demog_eng', '')
            firlanv = request.form.get('demog_firlan', '')
            ageengv = request.form.get('demog_ageeng', '')
            hislatv = request.form.get('demog_hislat', '')
            racev   = request.form.get('demog_race', '')

            insert_demo = """
                INSERT INTO tb11_profile (
                    uid, sid,
                    dobMonth, dobDay, dobYear, dobSum,
                    age, gender, edu, natEng, firLan,
                    ageEng, hisLat, race
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_demo, (
                uid, sid,
                bmv, bdv, byv, bsv,
                agev, genv, eduv, natengv, firlanv,
                ageengv, hislatv, racev
            ))
            link.commit()

        # save_url
        pageTypeID = "prac_instruction"
        pageTitle  = "Prac: Instruction"
        save_url(uid, sid, "", "", "", "", pageTypeID, pageTitle, request.url)
        link.commit()

    except Exception as e:
        print(f"Error in /prac_instruction route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template('prac_instruction.html')


# ----------------------------------------------------
#  PRAC_A
# ----------------------------------------------------
@app.route('/prac_a', methods=['GET', 'POST'])
def prac_a():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    subtop_param = request.args.get('subtop', '')
    last_page = request.args.get('lastPage', '')

    link = None
    visited_subtop = []
    try:
        link = get_db_connection()
        cursor = link.cursor()

        # If fid in [begin, next], start a new practice "taskTime"
        if fid == "begin":
            print("oh yes it is a one")
            session['startUnixTime'] = int(time.time())
            session['startTimeStamp'] = get_time_stamp_cdt()
            session['remainingTime'] = 30000
            session['lastPageSwitchUnixTime'] = int(time.time())

            # Insert into tb16_prac_taskTime with placeholders
            insert_time = """
                INSERT INTO tb16_prac_taskTime
                    (uid, sid, topID, timeStart, timeEnd, timeStartStamp, timeEndStamp)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
            """
            topID = "1"
            cursor.execute(insert_time, (
                uid, sid, topID,
                session['startUnixTime'],
                0,  # placeholder for timeEnd
                session['startTimeStamp'],
                ""  # placeholder for timeEndStamp
            ))

            session['visitedSub'] = ""
            visited_subtop = []

        elif fid in ["back", "next"]:
            print("oh yes it is a two", subtop_param)
            session['lastPageSwitchUnixTime'] = int(time.time())
            current = session.get('visitedSub', '')
            if current:
                session['visitedSub'] = current + ',' + subtop_param
            else:
                session['visitedSub'] = subtop_param
            visited_subtop = visited_subtop.append(subtop_param)
            print("ohhhh yeahhh baby dolll")
            print(visited_subtop, session['visitedSub'])

        # Load subtopics
        subtop_query = "SELECT * FROM tb13_prac_subtopic WHERE topID=%s ORDER BY subtopID"
        cursor.execute(subtop_query, ("1",))
        all_subtops = []
        subtopics = cursor.fetchall()
        for row in subtopics:
            all_subtops.append(row[0])

        print(all_subtops)
        # If lastPage == c3, maybe update c3Ans
        if last_page == "c3" and request.method == 'POST':
            print("yess yess ut's a c3")
            print(visited_subtop, all_subtops)
            ans = request.form.get('ans', '')
            passid_to_save = request.form.get('savepassid', '')
            if ans:
                update_ans = """
                    UPDATE tb15_prac_passQop
                    SET c3Ans=%s
                    WHERE sid=%s AND uid=%s AND passID=%s
                """
                cursor.execute(update_ans, (ans, sid, uid, passid_to_save))
            visited_subtop = split_subtopics(session.get('visitedSub', ''))
            visited_subtop.sort()
            if visited_subtop == all_subtops:
                # action_url = url_for('prac_k2', lastPage='c3')
                print("yesss it is ")
                return redirect(url_for('prac_k2', lastPage='c3'))

        link.commit()

        # Load topic from tb12_prac_topic
        topic_query = "SELECT * FROM tb12_prac_topic WHERE topID=%s"
        cursor.execute(topic_query, ("1",))
        topic_result = cursor.fetchone()

        # save_url
        pageTypeID = "prac_a"
        pageTitle  = f"a Prac: {topic_result[1]}" if topic_result else "a Prac"
        save_url(uid, sid, "", "", "", "", pageTypeID, pageTitle, request.url)

        # define redirect if timer runs out
        session['redirectPage'] = url_for('prac_k2', lastPage='a')

        if not visited_subtop:
            print("Diffferent caseesese")
            visited_subtop = split_subtopics(session.get('visitedSub', ''))
        
        return render_template('prac_a.html',
                               topic_result=topic_result,
                               subtopics=subtopics,
                               visited_subtop=visited_subtop)

    except Exception as e:
        print(f"Error in /prac_a route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

def split_subtopics(visited_sub_str):
    result =  visited_sub_str.split(",") if visited_sub_str else []
    print("Insideeeee splitted")
    print(result)
    # for i in range(0, len(visited_sub_str), 4):
    #     chunk = visited_sub_str[i:i+4]
    #     result.append(chunk)
    return result


# ----------------------------------------------------
#  PRAC_B
# ----------------------------------------------------
@app.route('/prac_b', methods=['GET', 'POST'])
def prac_b():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    subtopID = request.args.get('subtop', '')
    passOrd  = request.args.get('passOrd', '01')
    lastPage = request.args.get('lastPage', '')

    topID = "1"
    conID = "1"

    try:
        passOrderInt = int(passOrd)
    except ValueError:
        passOrderInt = 1

    passID = f"{subtopID}{conID}{passOrderInt}"
    nextPassOrder = passOrderInt + 1

    link = None
    pass_result = None

    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)

        print("yessssssssssssss")
        print(topID, subtopID, conID, str(passOrderInt), passID, passOrd)

        # Load passage
        pass_qry = """
            SELECT * 
            FROM tb14_prac_passage
            WHERE topID=%s AND subtopID=%s AND conID=%s AND passOrder=%s
        """
        cursor.execute(pass_qry, (topID, subtopID, conID, "0" + str(passOrderInt)))
        pass_result = cursor.fetchone()

        # save_url
        pageTypeID = "prac_b"
        passTitle = pass_result['passTitle'] if pass_result else ""
        pageTitle = f"b Prac: {passTitle}"
        save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

        session['subtopID']      = subtopID
        session['passID']        = passID
        session['passOrder']     = passOrderInt
        session['nextPassOrder'] = nextPassOrder
        session['passTitle']     = pageTitle

        now = int(time.time())
        if lastPage == "a":
            used_time = now - session.get('lastPageSwitchUnixTime', now)
            session['remainingTime'] = session.get('remainingTime', 0) - used_time
            session['lastPageSwitchUnixTime'] = now
            session['redirectPage'] = url_for('prac_c1', fid='done')

        elif lastPage == "c3":
            session['lastPageSwitchUnixTime'] = now
            session['redirectPage'] = url_for('prac_c1', fid='done')

            if request.method == 'POST':
                ans_to_save = request.form.get('ans', '')
                passid_to_save = request.form.get('savepassid', '')
                if ans_to_save:
                    updateAns = """
                        UPDATE tb15_prac_passQop
                        SET c3Ans=%s
                        WHERE sid=%s AND uid=%s AND passID=%s
                    """
                    cursor.execute(updateAns, (ans_to_save, sid, uid, passid_to_save))

        link.commit()

    except Exception as e:
        print(f"Error in /prac_b route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    return render_template('prac_b.html',
                           passResult=pass_result,
                           passOrder=passOrderInt)

def save_pass_answer(qid, ans_to_save, table="tb5_passQop"):
    """
    Saves the passage answer based on question ID.
    For qid == "c1": INSERT a new record with c1Ans.
    For qid == "c2": UPDATE the record setting c2Ans.
    For qid == "c3": UPDATE the record setting c3Ans.
    The table parameter allows using a different table (e.g. for practice pages).
    """
    uid = session.get('uid')
    sid = session.get('sid', '')
    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    passOrder = session.get('passOrder', 1)
    topID = "1"   # adjust if needed
    conID = "1"    # adjust if needed
    try:
        link = get_db_connection()
        cursor = link.cursor()
        if qid == "c1":
            query = f"""
                INSERT INTO {table} (uid, sid, topID, subtopID, conID, passID, passOrder, c1Ans)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (uid, sid, topID, subtopID, conID, passID, passOrder, ans_to_save))
        elif qid == "c2":
            query = f"""
                UPDATE {table}
                SET c2Ans = %s
                WHERE sid = %s AND uid = %s AND passID = %s
            """
            cursor.execute(query, (ans_to_save, sid, uid, passID))
        elif qid == "c3":
            query = f"""
                UPDATE {table}
                SET c3Ans = %s
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

# ----------------------------------------------------
#  PRAC_C1
# ----------------------------------------------------
@app.route('/prac_c1', methods=['GET', 'POST'])
def prac_c1():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    print(fid)
    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    passTitle = session.get('passTitle', '')
    topID = "1"
    conID = "1"
    pageTypeID = "prac_c1"
    pageTitle = f"C1: {passTitle}"
    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    # Update remaining time
    now = int(time.time())
    last_switch = session.get('lastPageSwitchUnixTime', now)
    session['remainingTime'] = session.get('remainingTime', 0) - (now - last_switch)
    session['lastPageSwitchUnixTime'] = now

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c1")  # expect "c1" here
        if ans:
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            return redirect(url_for('prac_c2', fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("prac_c1.html", fid=fid)


# ----------------------------------------------------
#  PRAC_C2
# ----------------------------------------------------
@app.route('/prac_c2', methods=['GET', 'POST'])
def prac_c2():
    print("yessssss c2 is here bro")
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    print(fid)
    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    passTitle = session.get('passTitle', '')
    passOrder = session.get('passOrder', 1)
    topID = "1"
    conID = "1"
    pageTypeID = "prac_c2"
    pageTitle = f"C2: {passTitle}"
    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        print("yeah baby")
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c2")
        if ans:
            print("yess inside thissss")
            save_pass_answer(qid, ans, table="tb15_prac_passQop")
            return redirect(url_for('prac_c3', fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("prac_c2.html", fid=fid)


# ----------------------------------------------------
#  PRAC_C3
# ----------------------------------------------------
@app.route('/prac_c3', methods=['GET', 'POST'])
def prac_c3():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    print("it's a c3 fucker")
    print(fid)
    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    passTitle = session.get('passTitle', '')
    topID = "1"
    conID = "1"
    nextPassOrder = session.get('nextPassOrder', 2)

    # Determine next action URL based on fid
    if fid == "same":
        action_url = url_for('prac_b', subtop=subtopID, passOrd=nextPassOrder, lastPage='c3')
    elif fid == "back":
        action_url = url_for('prac_a', fid='back', subtop=subtopID, lastPage='c3')
    elif fid == "done":
        action_url = url_for('prac_k2', lastPage='c3')
    else:
        action_url = url_for('prac_k2', lastPage='unknown')


    print("On yesss c3333")
    print(action_url)
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

    return render_template("prac_c3.html", fid=fid, action_url=action_url, passID=passID)


@app.route('/prac_k2', methods=['GET', 'POST'])
def prac_k2():
    """
    Equivalent to prac_k2.php
    """
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Hard-coded topID = '01' for practice
    topID = "1"

    lastPage = request.args.get('lastPage', '')

    link = None
    topic_title = ""
    subtop_string = ""

    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)

        # 1) If lastPage == 'c3' and we have a POST with ans => update c3Ans
        if lastPage == "c3" and request.method == 'POST':
            ans_to_save = request.form.get('ans', '')
            passid_to_save = request.form.get('savepassid', '')
            if ans_to_save:
                updateAns = """
                    UPDATE tb15_prac_passQop
                    SET c3Ans=%s
                    WHERE sid=%s AND uid=%s AND passID=%s
                """
                cursor.execute(updateAns, (ans_to_save, sid, uid, passid_to_save))

        # 2) Fetch the practice topic from tb12_prac_topic
        topic_q = "SELECT * FROM tb12_prac_topic WHERE topID=%s"
        cursor.execute(topic_q, (topID,))
        topic_row = cursor.fetchone()
        if topic_row:
            topic_title = topic_row['topTitle']  # or topic_row[1] if not using dict

        # 3) Build subtopic string from tb13_prac_subtopic
        subtop_q = "SELECT * FROM tb13_prac_subtopic WHERE topID=%s ORDER BY subtopID"
        cursor.execute(subtop_q, (topID,))
        subtop_rows = cursor.fetchall()
        # e.g. subtopString => "sub1, sub2, sub3"
        subtop_list = []
        for row in subtop_rows:
            subtop_list.append(row['subtopTitle'])
        subtop_string = ", ".join(subtop_list)

        # 4) save_url
        pageTypeID = "prac_k2"
        pageTitle  = f"K2 Prac: {topic_title}"
        save_url(
            uid=uid,
            sid=sid,
            topID=topID,
            subtopID="", 
            conID="", 
            passID="",
            pageTypeID=pageTypeID,
            pageTitle=pageTitle,
            url=request.url
        )

        link.commit()

    except Exception as e:
        print(f"Error in /prac_k2: {e}")
        return f"Database error: {e}", 500

    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 5) Render the prac_k2 template (final text area).
    #    The form will post to /instruction
    return render_template(
        'prac_k2.html',
        topicTitle=topic_title,
        subtopString=subtop_string,
        lastPage=lastPage
    )


@app.route('/instruction', methods=['GET', 'POST'])
def instruction():
    """
    Equivalent to instruction.php:
      - If there's a POST with textarea_k2, insert into tb18_prac_topicIdeas.
      - Sets topIDorder='01#' and conIDorder based on uid % 6.
      - Calls save_url with pageTypeID='instruction'.
      - Finally renders an instruction page with a form linking to /task_a?fid=begin.
    """
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    link = None
    topID = "1"  # from your code
    try:
        link = get_db_connection()
        cursor = link.cursor()

        # 1) If there's a POST with "textarea_k2", insert into tb18_prac_topicIdeas
        if request.method == 'POST':
            ans_to_save = request.form.get('textarea_k2', '').strip()
            if ans_to_save:
                insertAns = """
                    INSERT INTO tb18_prac_topicIdeas 
                        (uid, sid, topID, quesID, quesAns)
                    VALUES 
                        (%s, %s, %s, 'prac_k2', %s)
                """
                cursor.execute(insertAns, (uid, sid, topID, ans_to_save))

        # 2) Determine domain and condition order
        # domain => '01#'
        strDomain = "01#"

        # Condition Order depends on remainder = uid % 6
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
        else:  # remain == 0
            strCon = "3#2#1#3#2#1#3#2#1#3#2#1#"

        # 3) Update tb1_user with topIDorder and conIDorder
        updateUser = """
            UPDATE tb1_user
            SET topIDorder=%s, conIDorder=%s
            WHERE sid=%s AND uid=%s
        """
        cursor.execute(updateUser, (strDomain, strCon, sid, uid))

        # 4) save_url => instruction
        pageTypeID = "instruction"
        pageTitle  = "Instruction"
        save_url(
            uid=uid,
            sid=sid,
            topID=topID,
            subtopID="",
            conID="",
            passID="",
            pageTypeID=pageTypeID,
            pageTitle=pageTitle,
            url=request.url
        )

        link.commit()

    except Exception as e:
        print(f"Error in /instruction route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 5) Render the instruction.html page
    return render_template('instruction.html')

@app.route('/task_a', methods=['GET', 'POST'])
def task_a():
    """
    Equivalent to task_a.php:
      - GET fid = (begin|next|back|...) 
      - If fid in [begin, next], insert row into tb6_taskTime, reset visited subtopics
      - If fid == back, conDone++ in tb1_user, add visited subtopic
      - If lastPage == c3, update c3Ans in tb5_passQop from POST
      - Then load tb2_topic + tb3_subtopic, call save_url, set redirectPage
      - Render a template with the subtopic table + timer
    """
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # We'll assume a default topID is "1". If your code obtains it from session or DB, adjust here.
    topID = "1"

    # Parse query parameters
    fid = request.args.get('fid', '')
    lastPage = request.args.get('lastPage', '')
    subtop_param = request.args.get('subtop', '')

    link = None
    visited_subtop = []
    try:
        link = get_db_connection()
        cursor = link.cursor()

        # 1) If fid == begin or next => set up start time, insert into tb6_taskTime
        if fid == "begin":
            session['startUnixTime'] = int(time.time())
            # e.g. "Y-m-d H:i:s" in UTC-5
            session['startTimeStamp'] = get_time_stamp_cdt()
            # 60 seconds for debugging, or 900 for 15 minutes
            session['remainingTime'] = 30000
            session['lastPageSwitchUnixTime'] = int(time.time())

            insert_time = """
                INSERT INTO tb6_taskTime 
                    (uid, sid, topID, timeStart, timeEnd, timeStartStamp, timeEndStamp)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s)
            """
            topID = "1"
            cursor.execute(insert_time, (
                uid, sid, topID,
                session['startUnixTime'],
                0,  # Provide 0 for timeEnd
                session['startTimeStamp'],
                ""  # Provide an empty string for timeEndStamp
            ))

            # Start a session visitedSub = ""
            session['visitedSub'] = ""
            visited_subtop = []

        # 2) If fid == back => conDone++ in tb1_user, record visited subtopic
        elif fid in ["back", "next"]:
            # lastPage must be c4 or something => we don't update remaining time
            session['lastPageSwitchUnixTime'] = int(time.time())

            updateCon = """
                UPDATE tb1_user 
                SET conDone = conDone + 1 
                WHERE sid=%s AND uid=%s
            """
            cursor.execute(updateCon, (sid, uid))

            # add visited subtopic from ?subtop=XYZ
            current = session.get('visitedSub', '')
            if current:
                session['visitedSub'] = current + ',' + subtop_param
            else:
                session['visitedSub'] = subtop_param
            visited_subtop = visited_subtop.append(subtop_param)
            # session['visitedSub'] = session.get('visitedSub', '') + subtop_param
            # visited_subtop = visited_subtop.append(subtop_param)

        # 3) If lastPage == c3 => update c3Ans in tb5_passQop from POST
        subtop_q = "SELECT * FROM tb3_subtopic WHERE topID=%s ORDER BY subtopID"
        cursor.execute(subtop_q, (topID,))
        subtopics = cursor.fetchall()
        all_subtops = []
        for row in subtopics:
            all_subtops.append(row[0])

        print(all_subtops, lastPage)
        print("Oh yeahhhhhh babyyyy dollllll")
        
        if lastPage == "c4" and request.method == 'POST':
            print("yess its the final one and nothing to do else")
            ans_to_save = request.form.get('ans', '')
            passid_to_save = request.form.get('savepassid', '')
            if ans_to_save:
                updateAns = """
                    UPDATE tb5_passQop
                    SET c3Ans=%s
                    WHERE sid=%s AND uid=%s AND passID=%s
                """
                cursor.execute(updateAns, (ans_to_save, sid, uid, passid_to_save))
            visited_subtop = split_subtopics(session.get('visitedSub', ''))
            visited_subtop.sort()
            if visited_subtop == all_subtops:
                # action_url = url_for('prac_k2', lastPage='c3')
                print("yesss it is c4c4c44c4c4")
                return redirect(url_for('k2', lastPage='c4'))

        # 4) Load topic from tb2_topic
        topic_q = "SELECT * FROM tb2_topic WHERE topID=%s"
        cursor.execute(topic_q, (topID,))
        topicResult = cursor.fetchone()

        # 5) Load subtopics from tb3_subtopic
        subtop_q = "SELECT * FROM tb3_subtopic WHERE topID=%s ORDER BY subtopID"
        cursor.execute(subtop_q, (topID,))
        subtopics = cursor.fetchall()

        # 6) save_url => pageTypeID="a"
        pageTypeID = "a"
        pageTitle  = topicResult[1] if topicResult else "Unknown Topic"
        save_url(
            uid=uid,
            sid=sid,
            topID=topID,
            subtopID="",
            conID="",
            passID="",
            pageTypeID=pageTypeID,
            pageTitle=pageTitle,
            url=request.url
        )

        # 7) Set redirect page for timer
        session['redirectPage'] = url_for('k2', lastPage='a')
        # You can convert "k2.php?lastPage=a" to a Flask route if needed, e.g. url_for('k2', lastPage='a')

        link.commit()

        # If we haven't set visited_subtop yet, parse from session
        if not visited_subtop:
            print("different caseee")
            visited_subtop = split_subtopics(session.get('visitedSub', ''))

        # 8) Render template (task_a.html) passing topicResult + subtopics + visited_subtop
        return render_template(
            'task_a.html',
            topicResult=topicResult,
            subtopics=subtopics,
            visited_subtop=visited_subtop
        )

    except Exception as e:
        print(f"Error in /task_a route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

@app.route('/task_b', methods=['GET', 'POST'])
def task_b():
    """
    Equivalent to task_b.php
      - GET subtop (subtopic ID), passOrd, lastPage
      - Build passID, nextPassOrder
      - Fetch passage from tb4_passage
      - Update timer/remainingTime if lastPage == 'a'
      - If lastPage == 'c3', allow updating c3Ans in tb5_passQop
      - Store session variables for subtopID, passID, passOrder, etc.
      - Render a 'task_b.html' template displaying the article, timer, 
        links to /task_c1?fid=back or /task_c1?fid=same
    """
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Hard-code or retrieve from session if needed
    topID = "1"
    conID = "1"

    subtopID  = request.args.get('subtop', '')
    passOrd   = request.args.get('passOrd', '01')
    lastPage  = request.args.get('lastPage', '')

    try:
        passOrderInt = int(passOrd)
    except ValueError:
        passOrderInt = 1

    passID = f"{subtopID}{conID}{passOrderInt}"
    nextPassOrder = passOrderInt + 1

    link = None
    passResult = None

    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)

        # 1) Fetch the relevant passage from tb4_passage
        finPassOrdInt = ""
        if len(str(passOrderInt)) == 1:
            finPassOrdInt = "0" + str(passOrderInt)
        else:
            finPassOrdInt = str(passOrderInt)

        pass_qry = """
            SELECT * 
            FROM tb4_passage
            WHERE topID=%s AND subtopID=%s AND conID=%s AND passOrder=%s
        """
        cursor.execute(pass_qry, (topID, subtopID, conID, finPassOrdInt))
        passResult = cursor.fetchone()

        # 2) save_url => pageTypeID="b"
        pageTypeID = "b"
        pageTitle  = passResult['passTitle'] if passResult else "No Title"
        save_url(
            uid=uid,
            sid=sid,
            topID=topID,
            subtopID=subtopID,
            conID=conID,
            passID=passID,
            pageTypeID=pageTypeID,
            pageTitle=pageTitle,
            url=request.url
        )

        # 3) Store passage info in session
        session['subtopID']     = subtopID
        session['passID']       = passID
        session['passOrder']    = passOrderInt
        session['nextPassOrder']= nextPassOrder
        session['passTitle']    = pageTitle

        # 4) Timer logic
        now = int(time.time())

        if lastPage == "a":
            # Subtract time used
            used_time = now - session.get('lastPageSwitchUnixTime', now)
            session['remainingTime'] = session.get('remainingTime', 0) - used_time
            session['lastPageSwitchUnixTime'] = now
            # The redirect if time is up => /task_c1?fid=done
            session['redirectPage'] = url_for('task_c1', fid='done')

        elif lastPage == "c3":
            # Do not update remainingTime
            session['lastPageSwitchUnixTime'] = now
            session['redirectPage'] = url_for('task_c1', fid='done')

            # If there's an 'ans' posted, update c3Ans in tb5_passQop
            if request.method == 'POST':
                ans_to_save = request.form.get('ans', '')
                passid_to_save = request.form.get('savepassid', '')
                if ans_to_save:
                    updateAns = """
                        UPDATE tb5_passQop
                        SET c3Ans=%s
                        WHERE sid=%s AND uid=%s AND passID=%s
                    """
                    cursor.execute(updateAns, (ans_to_save, sid, uid, passid_to_save))

        link.commit()

    except Exception as e:
        print(f"Error in /task_b route: {e}")
        return f"Database error: {e}", 500
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 5) Render the template
    return render_template(
        'task_b.html',
        passResult=passResult,
        passOrder=passOrderInt
    )

@app.route('/task_c1', methods=['GET', 'POST'])
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
            return redirect(url_for('task_c2', fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("task_c1.html", fid=fid)

@app.route('/task_c2', methods=['GET', 'POST'])
def task_c2():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    passTitle = session.get('passTitle', '')
    passOrder = session.get('passOrder', 1)
    topID = "1"
    conID = "1"
    pageTypeID = "c2"
    pageTitle = f"C2: {passTitle}"
    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c2")
        if ans:
            save_pass_answer(qid, ans, table="tb5_passQop")
            return redirect(url_for('task_c3', fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("task_c2.html", fid=fid)


@app.route('/task_c3', methods=['GET', 'POST'])
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
    nextPassOrder = session.get('nextPassOrder', 2)

    pageTypeID = "c3"
    pageTitle = f"C3: {passTitle}"
    save_url(uid, sid, topID, subtopID, conID, passID, pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c3")
        if ans:
            save_pass_answer(qid, ans, table="tb5_passQop")
            return redirect(url_for('task_c4', fid=fid))
        else:
            return "No answer provided.", 400

    return render_template("task_c3.html", fid=fid, passID=passID)


@app.route('/task_c4', methods=['GET', 'POST'])
def task_c4():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    fid = request.args.get('fid', '')
    # Determine next action URL based on fid:
    if fid == "same":
        action_url = url_for('task_b', subtop=session.get('subtopID', ''), passOrd=session.get('nextPassOrder', 1), lastPage='c4')
    elif fid == "back":
        action_url = url_for('task_a', fid='back', subtop=session.get('subtopID', ''), lastPage='c4')
    elif fid == "done":
        action_url = url_for('k1', lastPage='c4')
    else:
        action_url = url_for('k1', lastPage='unknown')

    subtopID = session.get('subtopID', '')
    passID = session.get('passID', '')
    pageTypeID = "c4"
    passTitle = session.get('passTitle', '')
    pageTitle = f"C4: {passTitle}"
    save_url(uid, sid, "", "", "", "", pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans = request.form.get("ans", "").strip()
        qid = request.form.get("qid", "c4")
        if ans:
            # If you want to save a c4 answer, call save_pass_answer; (currently commented out in original)
            # save_pass_answer(qid, ans, table="tb5_passQop")
            return redirect(action_url)
        else:
            return "No answer provided.", 400

    return render_template("task_c4.html", fid=fid, action_url=action_url)
@app.route('/task_c4_redirect')
def task_c4_redirect():
    fid = request.args.get('fid')
    if fid == 'same':
        return redirect(url_for('task_b'))
    elif fid == 'back':
        return redirect(url_for('task_a'))
    elif fid == 'done':
        return redirect(url_for('k1'))
    else:
        return "Invalid parameter"

@app.route('/vocab', methods=['GET', 'POST'])
def vocab():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Next action: the done page (assumed to be served by a route named 'done')
    action_url = url_for('done')

    # Log the visit using save_url
    topID = "1"  # Adjust if necessary
    pageTypeID = "vocab"
    pageTitle = "Start Vocabulary Test"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    # Process vocabulary answers if form is submitted
    if request.method == "POST" and request.form.get("voc1", "").strip() != "":
        # Retrieve answers for voc1 through voc15
        voc1  = request.form.get("voc1", "").strip()
        voc2  = request.form.get("voc2", "").strip()
        voc3  = request.form.get("voc3", "").strip()
        voc4  = request.form.get("voc4", "").strip()
        voc5  = request.form.get("voc5", "").strip()
        voc6  = request.form.get("voc6", "").strip()
        voc7  = request.form.get("voc7", "").strip()
        voc8  = request.form.get("voc8", "").strip()
        voc9  = request.form.get("voc9", "").strip()
        voc10 = request.form.get("voc10", "").strip()
        voc11 = request.form.get("voc11", "").strip()
        voc12 = request.form.get("voc12", "").strip()
        voc13 = request.form.get("voc13", "").strip()
        voc14 = request.form.get("voc14", "").strip()
        voc15 = request.form.get("voc15", "").strip()

        aryUserInput = [voc1, voc2, voc3, voc4, voc5,
                        voc6, voc7, voc8, voc9, voc10,
                        voc11, voc12, voc13, voc14, voc15]
        # Right answers as given in saveVocab.php:
        aryRightAnswer = ["1", "2", "2", "4", "1", "3", "1", "1", "4", "5",
                          "3", "4", "1", "3", "5"]

        numCorrect = 0
        numWrong = 0
        numNotSure = 0

        for i in range(15):
            if aryUserInput[i] == aryRightAnswer[i]:
                numCorrect += 1
            else:
                if aryUserInput[i] == "6":
                    numNotSure += 1
                else:
                    numWrong += 1

        vocScore = (1 * numCorrect) - (0.2 * numWrong)

        try:
            link = get_db_connection()
            cursor = link.cursor()
            update_query = """
                UPDATE tb11_profile
                SET voc1=%s, voc2=%s, voc3=%s, voc4=%s, voc5=%s,
                    voc6=%s, voc7=%s, voc8=%s, voc9=%s, voc10=%s,
                    voc11=%s, voc12=%s, voc13=%s, voc14=%s, voc15=%s,
                    vocScore=%s
                WHERE sid=%s AND uid=%s
            """
            cursor.execute(update_query, (
                voc1, voc2, voc3, voc4, voc5,
                voc6, voc7, voc8, voc9, voc10,
                voc11, voc12, voc13, voc14, voc15,
                vocScore, sid, uid
            ))
            link.commit()
        except Exception as e:
            print(f"Error updating vocabulary answers: {e}")
            return f"Database error: {e}", 500
        finally:
            if link and link.is_connected():
                cursor.close()
                link.close()

        return redirect(action_url)

    return render_template("vocab.html", action_url=action_url)


# @app.route('/let_comp_one', methods=['GET', 'POST'])
# def let_comp_one():
#     uid = session.get('uid')
#     sid = session.get('sid', '')
#     if not uid:
#         return "No user session found; please start from the beginning.", 400

#     # The next step after saving answers will be the instructions page
#     next_action = url_for('let_comp_two_inst')

#     # Log the visit
#     topID = "1"  # adjust as needed
#     pageTypeID = "submit_lc1"
#     pageTitle = "Submit Letter Comparison One"
#     save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

#     if request.method == "POST":
#         # Process the letter comparison answers only if lc1 is provided.
#         lc1v = request.form.get("lc1", "").strip()
#         if lc1v != "":
#             lc2v = request.form.get("lc2", "").strip()
#             lc3v = request.form.get("lc3", "").strip()
#             lc4v = request.form.get("lc4", "").strip()
#             lc5v = request.form.get("lc5", "").strip()
#             lc6v = request.form.get("lc6", "").strip()
#             lc7v = request.form.get("lc7", "").strip()
#             lc8v = request.form.get("lc8", "").strip()
#             lc9v = request.form.get("lc9", "").strip()
#             lc10v = request.form.get("lc10", "").strip()
            
#             aryUserInput = [lc1v, lc2v, lc3v, lc4v, lc5v, lc6v, lc7v, lc8v, lc9v, lc10v]
#             aryRightAnswer = ["S", "D", "D", "D", "D", "S", "S", "D", "S", "D"]
            
#             numCorrect = sum(1 for i in range(10) if aryUserInput[i] == aryRightAnswer[i])
#             # numWrong = 10 - numCorrect (not used, since wrong contributes 0)
#             lcOneScore = numCorrect  # Each correct counts 1 point
            
#             try:
#                 link = get_db_connection()
#                 cursor = link.cursor()
#                 update_query = """
#                     UPDATE tb11_profile
#                     SET lc1=%s, lc2=%s, lc3=%s, lc4=%s, lc5=%s,
#                         lc6=%s, lc7=%s, lc8=%s, lc9=%s, lc10=%s, lcOneScore=%s
#                     WHERE sid=%s AND uid=%s
#                 """
#                 cursor.execute(update_query, (
#                     lc1v, lc2v, lc3v, lc4v, lc5v,
#                     lc6v, lc7v, lc8v, lc9v, lc10v,
#                     lcOneScore, sid, uid
#                 ))
#                 link.commit()
#             except Exception as e:
#                 print(f"Error updating letter comparison one: {e}")
#                 return f"Database error: {e}", 500
#             finally:
#                 if link and link.is_connected():
#                     cursor.close()
#                     link.close()

#             # After saving answers, redirect to the next step
#             return redirect(next_action)
#         else:
#             return "No answers provided.", 400

#     # For GET requests, render the form for letter comparison one.
#     return render_template("let_comp_one.html", action_url=next_action)


# @app.route('/let_comp_one_inst', methods=['GET', 'POST'])
# def let_comp_one_inst():
#     uid = session.get('uid')
#     sid = session.get('sid', '')
#     if not uid:
#         return "No user session found; please start from the beginning.", 400

#     # Assume topID is defined as "1" (adjust if needed)
#     topID = "1"

#     # Save URL (log the visit)
#     pageTypeID = "inst_lci1"
#     pageTitle = "Instruction for Letter Comparison One"
#     save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

#     # If POST and textarea_k2 is provided, insert answer into tb8_topicIdeas
#     if request.method == "POST":
#         ans_to_save = request.form.get("textarea_k2", "").strip()
#         if ans_to_save:
#             try:
#                 link = get_db_connection()
#                 cursor = link.cursor()
#                 insert_query = """
#                     INSERT INTO tb8_topicIdeas (uid, sid, topID, quesID, quesAns)
#                     VALUES (%s, %s, %s, %s, %s)
#                 """
#                 cursor.execute(insert_query, (uid, sid, topID, 'k2', ans_to_save))
#                 link.commit()
#             except Exception as e:
#                 print(f"Error inserting topic idea: {e}")
#                 return f"Database error: {e}", 500
#             finally:
#                 cursor.close()
#                 link.close()

#     # Render the instruction template
#     return render_template("let_comp_one_inst.html")

@app.route('/let_comp_one_inst', methods=['GET', 'POST'])
def let_comp_one_inst():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Use fixed topID (adjust as needed)
    topID = "1"
    pageTypeID = "inst_lci1"
    pageTitle = "Instruction for Letter Comparison One"
    # Log this page visit
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        ans_to_save = request.form.get("textarea_k2", "").strip()
        # if ans_to_save:
        try:
            link = get_db_connection()
            cursor = link.cursor()
            insert_query = """
                INSERT INTO tb8_topicIdeas (uid, sid, topID, quesID, quesAns)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (uid, sid, topID, "k2", ans_to_save))
            link.commit()
        except Exception as e:
            print(f"Error inserting topic idea: {e}")
            return f"Database error: {e}", 500
        finally:
            if link and link.is_connected():
                cursor.close()
                link.close()
        # Redirect to Letter Comparison One page
        return redirect(url_for('let_comp_one'))
        # else:
        #     return "No answer provided.", 400

    return render_template("let_comp_one_inst.html")


@app.route('/let_comp_one', methods=['GET', 'POST'])
def let_comp_one():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Next action: letter comparison two instruction page.
    next_action = url_for('let_comp_two_inst')
    topID = "1"
    pageTypeID = "start_lc1"
    pageTitle = "Start Letter Comparison One"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    if request.method == "POST":
        # Retrieve LC1 answers from the form (fields: lc1 to lc10)
        lc1 = request.form.get("lc1", "").strip()
        if lc1 == "":
            return "No answer provided.", 400
        lc2 = request.form.get("lc2", "").strip()
        lc3 = request.form.get("lc3", "").strip()
        lc4 = request.form.get("lc4", "").strip()
        lc5 = request.form.get("lc5", "").strip()
        lc6 = request.form.get("lc6", "").strip()
        lc7 = request.form.get("lc7", "").strip()
        lc8 = request.form.get("lc8", "").strip()
        lc9 = request.form.get("lc9", "").strip()
        lc10 = request.form.get("lc10", "").strip()

        aryUserInput = [lc1, lc2, lc3, lc4, lc5, lc6, lc7, lc8, lc9, lc10]
        aryRightAnswer = ["S", "D", "D", "D", "D", "S", "S", "D", "S", "D"]

        numCorrect = sum(1 for i in range(10) if aryUserInput[i] == aryRightAnswer[i])
        # Compute score (each correct = 1 point)
        lcOneScore = numCorrect

        try:
            link = get_db_connection()
            cursor = link.cursor()
            update_query = """
                UPDATE tb11_profile
                SET lc1=%s, lc2=%s, lc3=%s, lc4=%s, lc5=%s,
                    lc6=%s, lc7=%s, lc8=%s, lc9=%s, lc10=%s,
                    lcOneScore=%s
                WHERE sid=%s AND uid=%s
            """
            cursor.execute(update_query, (
                lc1, lc2, lc3, lc4, lc5,
                lc6, lc7, lc8, lc9, lc10,
                lcOneScore, sid, uid
            ))
            link.commit()
        except Exception as e:
            print(f"Error updating LC1 answers: {e}")
            return f"Database error: {e}", 500
        finally:
            if link and link.is_connected():
                cursor.close()
                link.close()

        return redirect(next_action)

    return render_template("let_comp_one.html", action_url=next_action)



@app.route('/let_comp_two_inst', methods=['GET', 'POST'])
def let_comp_two_inst():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Assume topID is "1" if needed
    topID = "1"

    # Save URL with pageTypeID "inst_lc2" and appropriate title
    pageTypeID = "inst_lc2"
    pageTitle = "Instruction for Letter Comparison Two"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    # If form was submitted and lc1 is not empty, process the answers
    if request.method == "POST" and request.form.get("lc1", "").strip() != "":
        lc1v = request.form.get("lc1", "").strip()
        lc2v = request.form.get("lc2", "").strip()
        lc3v = request.form.get("lc3", "").strip()
        lc4v = request.form.get("lc4", "").strip()
        lc5v = request.form.get("lc5", "").strip()
        lc6v = request.form.get("lc6", "").strip()
        lc7v = request.form.get("lc7", "").strip()
        lc8v = request.form.get("lc8", "").strip()
        lc9v = request.form.get("lc9", "").strip()
        lc10v = request.form.get("lc10", "").strip()

        aryUserInput = [lc1v, lc2v, lc3v, lc4v, lc5v, lc6v, lc7v, lc8v, lc9v, lc10v]
        aryRightAnswer = ["S", "D", "D", "D", "D", "S", "S", "D", "S", "D"]

        numCorrect = 0
        numWrong = 0
        for i in range(10):
            if aryUserInput[i] == aryRightAnswer[i]:
                numCorrect += 1
            else:
                numWrong += 1

        lcOneScore = numCorrect  # since wrong answers contribute 0

        try:
            link = get_db_connection()
            cursor = link.cursor()
            update_query = """
                UPDATE tb11_profile
                SET lc1=%s, lc2=%s, lc3=%s, lc4=%s, lc5=%s, lc6=%s, lc7=%s, lc8=%s, lc9=%s, lc10=%s, lcOneScore=%s
                WHERE sid=%s AND uid=%s
            """
            cursor.execute(update_query, (lc1v, lc2v, lc3v, lc4v, lc5v, lc6v, lc7v, lc8v, lc9v, lc10v, lcOneScore, sid, uid))
            link.commit()
        except Exception as e:
            print(f"Error updating letter comparison answers: {e}")
            return f"Database error: {e}", 500
        finally:
            if link and link.is_connected():
                cursor.close()
                link.close()

    # Render the instruction template for Letter Comparison Two
    return render_template("let_comp_two_inst.html")

@app.route('/let_comp_two', methods=['GET', 'POST'])
def let_comp_two():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Assume topID is "1"
    topID = "1"

    # Define the next action: vocabulary task
    action_url = url_for('vocab')  # Make sure you have a /vocab route

    # Log this page visit with save_url
    pageTypeID = "start_lc2"
    pageTitle = "Start Letter Comparison Two"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    # If POST, process LC2 answers
    if request.method == "POST" and request.form.get("lc11", "").strip() != "":
        # Retrieve LC2 answers from the form
        lc11v = request.form.get("lc11", "").strip()
        lc12v = request.form.get("lc12", "").strip()
        lc13v = request.form.get("lc13", "").strip()
        lc14v = request.form.get("lc14", "").strip()
        lc15v = request.form.get("lc15", "").strip()
        lc16v = request.form.get("lc16", "").strip()
        lc17v = request.form.get("lc17", "").strip()
        lc18v = request.form.get("lc18", "").strip()
        lc19v = request.form.get("lc19", "").strip()
        lc20v = request.form.get("lc20", "").strip()

        aryUserInput = [lc11v, lc12v, lc13v, lc14v, lc15v, lc16v, lc17v, lc18v, lc19v, lc20v]
        aryRightAnswer = ["D", "S", "S", "S", "D", "S", "D", "S", "D", "D"]

        numCorrect = sum(1 for i in range(10) if aryUserInput[i] == aryRightAnswer[i])
        # Wrong answers contribute 0, so score equals numCorrect
        lcTwoScore = numCorrect

        try:
            link = get_db_connection()
            cursor = link.cursor()
            update_query = """
                UPDATE tb11_profile
                SET lc11=%s, lc12=%s, lc13=%s, lc14=%s, lc15=%s,
                    lc16=%s, lc17=%s, lc18=%s, lc19=%s, lc20=%s, lcTwoScore=%s
                WHERE sid=%s AND uid=%s
            """
            cursor.execute(update_query, (
                lc11v, lc12v, lc13v, lc14v, lc15v,
                lc16v, lc17v, lc18v, lc19v, lc20v,
                lcTwoScore, sid, uid
            ))
            link.commit()
        except Exception as e:
            print(f"Error updating LC2 answers: {e}")
            return f"Database error: {e}", 500
        finally:
            if link and link.is_connected():
                cursor.close()
                link.close()

        # After saving, redirect to the vocabulary task.
        return redirect(action_url)

    # For GET, render the letter comparison two form.
    return render_template("let_comp_two.html", action_url=url_for('let_comp_two'))


CORRECT_ANSWERS = ["1", "2", "2", "4", "1", "3", "1", "1", "4", "5", "3", "4", "1", "3", "5"]


@app.route('/vocab_results')
def vocab_results():
    results = session.pop('vocab_results', None)
    if not results:
        return redirect(url_for('submit_vocab'))
        
    return render_template('vocab_results.html',
                         correct=results['correct'],
                         wrong=results['wrong'],
                         not_sure=results['not_sure'],
                         score=results['score'])

@app.route('/k2', methods=['GET', 'POST'])
def k2():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Assume topID is defined (hard-coded here as "1")
    topID = "1"

    # Query topic from tb2_topic
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tb2_topic WHERE topID = %s", (topID,))
        topic_row = cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving topic: {e}")
        return f"Database error: {e}", 500

    topicTitle = topic_row['topTitle'] if topic_row else "Unknown Topic"

    # Build subtopic string from tb3_subtopic
    subtop_list = []
    try:
        cursor.execute("SELECT * FROM tb3_subtopic WHERE topID = %s ORDER BY subtopID", (topID,))
        subtop_rows = cursor.fetchall()
        for row in subtop_rows:
            subtop_list.append(row['subtopTitle'])
    except Exception as e:
        print(f"Error retrieving subtopics: {e}")
    finally:
        cursor.close()
        link.close()

    subtopString = ", ".join(subtop_list)
    # Remove any leading comma and space (if any)
    trimSubtop = subtopString.lstrip(", ").strip()

    # Get lastPage from query parameters
    lastPage = request.args.get('lastPage', '')

    # If lastPage == "c3", process POST data: update c3Ans and update condition
    if lastPage == "c4" and request.method == "POST":
        ans_to_save = request.form.get('ans', '').strip()
        passid_to_save = request.form.get('savepassid', '')
        if ans_to_save:
            try:
                link = get_db_connection()
                cursor = link.cursor()
                update_query = """
                    UPDATE tb5_passQop 
                    SET c3Ans = %s 
                    WHERE sid = %s AND uid = %s AND passID = %s
                """
                cursor.execute(update_query, (ans_to_save, sid, uid, passid_to_save))
                # Also update condition done
                update_con = "UPDATE tb1_user SET conDone = conDone + 1 WHERE sid = %s AND uid = %s"
                cursor.execute(update_con, (sid, uid))
                link.commit()
            except Exception as e:
                print(f"Error updating c3Ans in /k2: {e}")
                return f"Database error: {e}", 500
            finally:
                cursor.close()
                link.close()

    # Save URL: log visit as pageTypeID "k2"
    pageTypeID = "k2"
    pageTitle_full = f"K2: {topicTitle}"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle_full, request.url)

    # Set redirectPage (for timer) to the next page; here, the original action is letCompOneInst.php,
    # so we assume that route is converted to Flask as 'let_comp_one_inst'
    redirect_url = url_for('let_comp_one_inst')
    
    # You might store redirect_url in session for timer use:
    session['redirectPage'] = redirect_url

    # The action for the form in this page should be the Flask route for letCompOneInst.
    # We'll assume that route is named 'let_comp_one_inst'.
    action_url = url_for('let_comp_one_inst')

    # Render the k2.html template with topicTitle and trimSubtop
    return render_template("k2.html", topicTitle=topicTitle, trimSubtop=trimSubtop, action_url=action_url)

def handle_c3_submission(cursor, request, session):
    ans = request.form.get('ans')
    savepassid = request.form.get('savepassid')
    if ans and savepassid:
        cursor.execute(
            "UPDATE tb5_passQop SET c3Ans = %s WHERE sid = %s AND uid = %s AND passID = %s",
            (ans, session['sid'], session['uid'], savepassid)
        )
    # Update condition done
    cursor.execute(
        "UPDATE tb1_user SET conDone = conDone + 1 WHERE sid = %s AND uid = %s",
        (session['sid'], session['uid'])
    )

@app.route('/done', methods=['GET', 'POST'])
def done():
    uid = session.get('uid')
    sid = session.get('sid', '')
    if not uid:
        return "No user session found; please start from the beginning.", 400

    # Assume topID is "1" (adjust if needed)
    topID = "1"

    # 1. Log the DONE page visit.
    pageTypeID = "DONE"
    pageTitle = "DONE"
    save_url(uid, sid, topID, "", "", "", pageTypeID, pageTitle, request.url)

    # 2. Process vocabulary answers if provided (POST).
    if request.method == "POST" and request.form.get("voc1", "").strip() != "":
        voc1 = request.form.get("voc1", "").strip()
        voc2 = request.form.get("voc2", "").strip()
        voc3 = request.form.get("voc3", "").strip()
        voc4 = request.form.get("voc4", "").strip()
        voc5 = request.form.get("voc5", "").strip()
        voc6 = request.form.get("voc6", "").strip()
        voc7 = request.form.get("voc7", "").strip()
        voc8 = request.form.get("voc8", "").strip()
        voc9 = request.form.get("voc9", "").strip()
        voc10 = request.form.get("voc10", "").strip()
        voc11 = request.form.get("voc11", "").strip()
        voc12 = request.form.get("voc12", "").strip()
        voc13 = request.form.get("voc13", "").strip()
        voc14 = request.form.get("voc14", "").strip()
        voc15 = request.form.get("voc15", "").strip()

        aryUserInput = [voc1, voc2, voc3, voc4, voc5,
                        voc6, voc7, voc8, voc9, voc10,
                        voc11, voc12, voc13, voc14, voc15]
        aryRightAnswer = ["1", "2", "2", "2", "3",
                          "2", "4", "1", "4", "5",
                          "3", "4", "1", "3", "5"]

        numCorrect = 0
        numWrong = 0
        numNotSure = 0

        for i in range(15):
            if aryUserInput[i] == aryRightAnswer[i]:
                numCorrect += 1
            else:
                if aryUserInput[i] == "6":
                    numNotSure += 1
                else:
                    numWrong += 1

        vocScore = (1 * numCorrect) - (0.2 * numWrong)

        try:
            link = get_db_connection()
            cursor = link.cursor()
            update_query = """
                UPDATE tb11_profile
                SET voc1=%s, voc2=%s, voc3=%s, voc4=%s, voc5=%s,
                    voc6=%s, voc7=%s, voc8=%s, voc9=%s, voc10=%s,
                    voc11=%s, voc12=%s, voc13=%s, voc14=%s, voc15=%s,
                    vocScore=%s
                WHERE sid=%s AND uid=%s
            """
            cursor.execute(update_query, (
                voc1, voc2, voc3, voc4, voc5,
                voc6, voc7, voc8, voc9, voc10,
                voc11, voc12, voc13, voc14, voc15,
                vocScore, sid, uid
            ))
            link.commit()
        except Exception as e:
            print(f"Error updating vocabulary answers: {e}")
            return f"Database error: {e}", 500
        finally:
            if link and link.is_connected():
                cursor.close()
                link.close()

    # 3. Update time intervals in output1_url.
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM output1_url
            WHERE topID=%s AND sid=%s AND uid=%s
            ORDER BY op1ID DESC
        """, (topID, sid, uid))
        op_results = cursor.fetchall()
        nextUnixTime = 0
        for row in op_results:
            rowID = row.get('op1ID', 0)
            if rowID > 0:
                thisUnixTime = row.get('unixTime', 0)
                if nextUnixTime:
                    timeInterval = abs(nextUnixTime - thisUnixTime)
                else:
                    timeInterval = 0
                if row.get('pageTypeID') != "DONE":
                    cursor.execute("UPDATE output1_url SET time_interval=%s WHERE op1ID=%s", (timeInterval, rowID))
                nextUnixTime = thisUnixTime
        link.commit()
    except Exception as e:
        print(f"Error updating time intervals: {e}")
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 4. Update passage reading time for pageTypeID 'b' (tb5_passQop).
    try:
        link = get_db_connection()
        cursor = link.cursor()
        cursor.execute("""
            SELECT * FROM output1_url
            WHERE sid=%s AND uid=%s AND pageTypeID='b'
        """, (sid, uid))
        for row in cursor.fetchall():
            qryPassID = row[6]  # adjust index as needed (passID)
            qryPassRT = row[9]  # adjust index for time_interval
            cursor.execute("""
                UPDATE tb5_passQop SET passRT=%s
                WHERE sid=%s AND uid=%s AND passID=%s
            """, (qryPassRT, sid, uid, qryPassID))
        link.commit()
    except Exception as e:
        print(f"Error updating passage reading time for b: {e}")
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 5. Update passage reading time for pageTypeID 'prac_b' (tb15_prac_passQop).
    try:
        link = get_db_connection()
        cursor = link.cursor()
        cursor.execute("""
            SELECT * FROM output1_url
            WHERE sid=%s AND uid=%s AND pageTypeID='prac_b'
        """, (sid, uid))
        for row in cursor.fetchall():
            qryPassID = row[6]  # adjust index if necessary
            qryPassRT = row[9]
            cursor.execute("""
                UPDATE tb15_prac_passQop SET passRT=%s
                WHERE sid=%s AND uid=%s AND passID=%s
            """, (qryPassRT, sid, uid, qryPassID))
        link.commit()
    except Exception as e:
        print(f"Error updating passage reading time for prac_b: {e}")
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 6. Update letter comparison one time (lcOneRT) from output1_url where pageTypeID='start_lc1'
    try:
        link = get_db_connection()
        cursor = link.cursor()
        cursor.execute("""
            SELECT * FROM output1_url
            WHERE sid=%s AND uid=%s AND pageTypeID='start_lc1'
        """, (sid, uid))
        lcOneRTResult = cursor.fetchone()
        if lcOneRTResult:
            qrylcOneRT = lcOneRTResult[9]  # adjust index for time_interval
            cursor.execute("""
                UPDATE tb11_profile SET lcOneRT=%s
                WHERE sid=%s AND uid=%s
            """, (qrylcOneRT, sid, uid))
            link.commit()
    except Exception as e:
        print(f"Error updating lcOneRT: {e}")
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 7. Update letter comparison two time (lcTwoRT) from output1_url where pageTypeID='start_lc2'
    try:
        link = get_db_connection()
        cursor = link.cursor()
        cursor.execute("""
            SELECT * FROM output1_url
            WHERE sid=%s AND uid=%s AND pageTypeID='start_lc2'
        """, (sid, uid))
        lcTwoRTResult = cursor.fetchone()
        if lcTwoRTResult:
            qrylcTwoRT = lcTwoRTResult[9]  # adjust index for time_interval
            cursor.execute("""
                UPDATE tb11_profile SET lcTwoRT=%s
                WHERE sid=%s AND uid=%s
            """, (qrylcTwoRT, sid, uid))
            link.commit()
    except Exception as e:
        print(f"Error updating lcTwoRT: {e}")
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 8. Process Topic Ideas - Bonus Words:
    try:
        link = get_db_connection()
        cursor = link.cursor(dictionary=True)
        # Get bonus words from tb2_topic (topIdeasBonusWords)
        cursor.execute("SELECT * FROM tb2_topic WHERE topID=%s", (topID,))
        topicRow = cursor.fetchone()
        topicIdeasBWsString = topicRow.get('topIdeasBonusWords', "") if topicRow else ""
        topicIdeasBWsArray = topicIdeasBWsString.split(" ") if topicIdeasBWsString else []

        # Get user's topic ideas answer from tb8_topicIdeas
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

        # Determine bonus words: words in user's answer that are in the bonus words array
        bonusWordsAry = []
        bonusWordsCnt = 0
        for word in topicIdeasAnsStringAry:
            if word and word in topicIdeasBWsArray:
                bonusWordsAry.append(word)
                bonusWordsCnt += 1

        bonusWordsMoney = 0.05 * bonusWordsCnt
        bonusWordsString = " ".join(bonusWordsAry)

        # Insert bonus words info into tb9_topicBonus
        insertBonusQry = """
            INSERT INTO tb9_topicBonus 
                (uid, sid, topID, quesID, quesAns, bonusWord, bonusWordCnt, bonusMoney)
            VALUES (%s, %s, %s, 'k2', %s, %s, %s, %s)
        """
        cursor.execute(insertBonusQry, (uid, sid, topID, topicIdeasAnsString, bonusWordsString, bonusWordsCnt, bonusWordsMoney))
        link.commit()
    except Exception as e:
        print(f"Error processing bonus words: {e}")
    finally:
        if link and link.is_connected():
            cursor.close()
            link.close()

    # 9. Compute mTurk unique code: 999 - uid
    try:
        mTurkUniCode = 999 - int(uid)
    except Exception:
        mTurkUniCode = 0

    final_code = f"9XQE783CE{mTurkUniCode}"
    
    # Render the final message template with bonusWordsCnt and final_code
    return render_template("done.html", bonusWordsCnt=bonusWordsCnt, final_code=final_code)

if __name__ == '__main__':
    # init_db()  # Initialize database on startup
    app.run(debug=True)