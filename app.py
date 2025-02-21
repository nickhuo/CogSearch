from flask import Flask, render_template, session, request, redirect, url_for, g
import sqlite3
import time
import os
from datetime import datetime
import click
# Add to existing imports
from werkzeug.exceptions import BadRequestKeyError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['DATABASE'] = os.path.join(app.instance_path, 'app.db')

# SQLite database configuration
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    os.makedirs(app.instance_path, exist_ok=True)
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('init-db')
def init_db_command():
    """Initialize the database."""
    init_db()
    print('Initialized the database.')

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Create schema.sql file
schema = """
DROP TABLE IF EXISTS tb1_user;

CREATE TABLE tb1_user (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    sid INTEGER NOT NULL,
    mturk_id TEXT NOT NULL,
    consent_time DATETIME NOT NULL,
    taskDone INTEGER DEFAULT 0,
    conDone INTEGER DEFAULT 0,
    topIDorder TEXT,
    conIDorder TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# Create instance folder and schema.sql if they don't exist
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)
with open(os.path.join(app.instance_path, 'schema.sql'), 'w') as f:
    f.write(schema)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/warning')
def warning():
    return render_template('warning.html')

@app.route('/consent', methods=['GET', 'POST'])
def consent():
    db = get_db()
    
    if 'sid' in session:
        session.clear()
    
    if request.method == 'POST':
        mturk_id = request.form.get('mturkid')
        consent_check = request.form.get('consentCheck')
        
        if not mturk_id or not consent_check:
            return render_template('consent.html', error='Please fill all required fields')
        
        try:
            cursor = db.cursor()
            
            # Get max UID
            cursor.execute("SELECT MAX(uid) as maxuid FROM tb1_user")
            result = cursor.fetchone()
            max_uid = result['maxuid'] if result['maxuid'] else 0
            sid = max_uid + 401
            
            # Create new user
            consent_time = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO tb1_user 
                (sid, mturk_id, consent_time, taskDone, conDone)
                VALUES (?, ?, ?, ?, ?)
            ''', (sid, mturk_id, consent_time, 0, 0))
            
            db.commit()
            
            # Set session variables
            session['sid'] = sid
            session['uid'] = cursor.lastrowid
            
            return redirect(url_for('demographic'))
            
        except sqlite3.Error as e:
            db.rollback()
            return render_template('consent.html', error=f'Database error: {str(e)}')
    
    return render_template('consent.html')

# Add new route for demographic form
@app.route('/demographic', methods=['GET', 'POST'])
def demographic():
    if 'uid' not in session:
        return redirect(url_for('consent'))
    
    db = get_db()
    error = None
    
    if request.method == 'POST':
        try:
            # Get form data
            dob_month = int(request.form['demog_bm'])
            dob_day = int(request.form['demog_bd'])
            dob_year = int(request.form['demog_by'])
            age = int(request.form['demog_age'])
            gender = int(request.form['demog_gen'])
            education = float(request.form['demog_edu'])
            is_native_english = bool(int(request.form['demog_eng']))
            is_hispanic_latino = bool(int(request.form['demog_hislat']))
            race = int(request.form['demog_race'])
            
            # Optional fields
            first_language = request.form.get('demog_firlan', '')
            english_acquisition_age = request.form.get('demog_ageeng', type=int)

            # Validate data
            if not (1 <= dob_month <= 12):
                raise ValueError("Invalid birth month")
            if not (1 <= dob_day <= 31):
                raise ValueError("Invalid birth day")
            if not (1900 <= dob_year <= 2015):
                raise ValueError("Invalid birth year")
            if not (18 <= age <= 100):
                raise ValueError("Invalid age")

            # Update user in database
            cursor = db.cursor()
            cursor.execute('''
                UPDATE tb1_user SET
                    dob_month = ?,
                    dob_day = ?,
                    dob_year = ?,
                    age = ?,
                    gender = ?,
                    education = ?,
                    is_native_english = ?,
                    first_language = ?,
                    english_acquisition_age = ?,
                    is_hispanic_latino = ?,
                    race = ?
                WHERE uid = ?
            ''', (
                dob_month, dob_day, dob_year,
                age, gender, education,
                is_native_english, first_language,
                english_acquisition_age, is_hispanic_latino,
                race, session['uid']
            ))
            db.commit()
            cursor.close()

            return redirect(url_for('prac_instruction'))

        except (BadRequestKeyError, ValueError, KeyError) as e:
            error = "Please fill all required fields correctly"
            db.rollback()
        except sqlite3.Error as e:
            error = f"Database error: {str(e)}"
            db.rollback()

    return render_template('demographic.html', error=error)

@app.route('/save_demog', methods=['POST'])
def save_demog():
    # Get form data
    bm = request.form['demog_bm']
    bd = request.form['demog_bd']
    by = request.form['demog_by']
    age = request.form['demog_age']
    gen = request.form['demog_gen']
    edu = request.form['demog_edu']
    nateng = request.form.get('demog_eng', 0)
    firlan = request.form.get('demog_firlan', '')
    ageeng = request.form.get('demog_ageeng', 0)
    hislat = request.form.get('demog_hislat', 0)
    race = request.form.get('demog_race', 0)

    # Save to database
    conn = get_db()
    cursor = conn.cursor()

    # Insert user data
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    insert_user_query = """
        INSERT INTO tb1_user (sid, taskDone, conDone, signedConsent, signedDate)
        VALUES (%s, 0, 0, 'TRUE', %s)
    """
    cursor.execute(insert_user_query, (session.get('sid'), timestamp))
    conn.commit()

    # Get the last inserted uid
    cursor.execute("SELECT MAX(uid) as uid FROM tb1_user WHERE sid=%s", (session.get('sid'),))
    user_result = cursor.fetchone()
    uid = user_result[0]

    # Save demographic data
    insert_demog_query = """
        INSERT INTO tb1_demog (uid, bm, bd, by, age, gen, edu, nateng, firlan, ageeng, hislat, race)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_demog_query, (uid, bm, bd, by, age, gen, edu, nateng, firlan, ageeng, hislat, race))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('prac_instruction'))

@app.route('/prac_instruction', methods=['GET', 'POST'])
def prac_instruction():
    if request.method == 'POST':
        # Save demographic answers
        bmv = request.form.get('demog_bm')
        bdv = request.form.get('demog_bd')
        byv = request.form.get('demog_by')
        agev = request.form.get('demog_age')
        genv = request.form.get('demog_gen')
        eduv = request.form.get('demog_edu')
        natengv = request.form.get('demog_eng')
        firlanv = request.form.get('demog_firlan')
        ageengv = request.form.get('demog_ageeng')
        hislatv = request.form.get('demog_hislat')
        racev = request.form.get('demog_race')

        if bmv:  # If demographic data is provided
            conn = get_db()
            cursor = conn.cursor()

            try:
                # Insert demographic data into tb11_profile
                insert_demo_query = """
                    INSERT INTO tb11_profile (uid, sid, dobMonth, dobDay, dobYear, dobSum, age, gender, edu, natEng, firLan, ageEng, hisLat, race)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                dob_sum = f"{bmv}/{bdv}/{byv}"
                cursor.execute(insert_demo_query, (
                    session.get('uid'), session.get('sid'), bmv, bdv, byv, dob_sum, agev, genv, eduv, natengv, firlanv, ageengv, hislatv, racev
                ))
                conn.commit()
            except Exception as e:
                print(f"Error saving demographic data: {e}")
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

    return render_template('prac_instruction.html')


@app.route('/prac_a', methods=['GET', 'POST'])
def prac_a():
    if 'uid' not in session:
        return redirect(url_for('index'))  # Redirect if user is not logged in

    uid = session['uid']
    sid = session.get('sid')
    topID = "01"  # Hardcoded for this example

    # Handle GET parameters
    fid = request.args.get('fid')
    last_page = request.args.get('lastPage')
    subtop = request.args.get('subtop')

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Set up start time and end time
        if fid in ["begin", "next"]:
            session['startUnixTime'] = int(time.time())
            session['startTimeStamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            session['remainingTime'] = 30  # Reduced time for debugging
            session['lastPageSwitchUnixTime'] = int(time.time())

            # Insert start time into database
            insert_time_query = """
                INSERT INTO tb16_prac_taskTime (uid, sid, topID, timeStart, timeStartStamp)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_time_query, (uid, sid, topID, session['startUnixTime'], session['startTimeStamp']))
            conn.commit()

            # Start a session to log visited subtopics
            session['visitedSub'] = ""
            visitedSubtop = []

        # Handle "back" action
        if fid == "back":
            session['lastPageSwitchUnixTime'] = int(time.time())

            # Add visited subtopic to the session
            if subtop:
                session['visitedSub'] += subtop
                visitedSubtop = list(session['visitedSub'])

        # Save c3 answer
        if last_page == "c3":
            ans_to_save = request.form.get('ans')
            passid_to_save = request.form.get('savepassid')

            if ans_to_save and passid_to_save:
                update_ans_query = """
                    UPDATE tb15_prac_passQop
                    SET c3Ans = ?
                    WHERE sid = ? AND uid = ? AND passID = ?
                """
                cursor.execute(update_ans_query, (ans_to_save, sid, uid, passid_to_save))
                conn.commit()

        # Fetch topic and subtopic data
        topic_query = "SELECT * FROM tb12_prac_topic WHERE topID = ?"
        cursor.execute(topic_query, (topID,))
        topic_result = cursor.fetchone()

        subtop_query = "SELECT * FROM tb13_prac_subtopic WHERE topID = ? ORDER BY subtopID"
        cursor.execute(subtop_query, (topID,))
        subtop_results = cursor.fetchall()

        # Define redirect page for timer
        session['redirectPage'] = "prac_k2?lastPage=a"

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return render_template('prac_a.html', topic=topic_result, subtopics=subtop_results, visitedSubtop=visitedSubtop)


@app.route('/prac_b', methods=['GET', 'POST'])
def prac_b():
    if 'uid' not in session:
        return redirect(url_for('index'))  # Redirect if user is not logged in

    uid = session['uid']
    sid = session.get('sid')
    topID = "01"  # Hardcoded for this example
    conID = "1"   # Hardcoded for this example

    # Get query parameters
    subtopID = request.args.get('subtop')
    passOrder = request.args.get('passOrd')
    lastPage = request.args.get('lastPage')

    # Generate passID and nextPassOrder
    passID = f"{subtopID}{conID}{passOrder}"
    nextPassOrder = int(passOrder) + 1

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Fetch article data
        pass_query = """
            SELECT * FROM tb14_prac_passage
            WHERE topID = ? AND subtopID = ? AND conID = ? AND passOrder = ?
        """
        cursor.execute(pass_query, (topID, subtopID, conID, passOrder))
        passResult = cursor.fetchone()

        if not passResult:
            return "Article not found", 404

        # Save URL and session data
        pageTitle = f"b Prac: {passResult['passTitle']}"
        session['subtopID'] = subtopID
        session['passID'] = passID
        session['passOrder'] = passOrder
        session['nextPassOrder'] = nextPassOrder
        session['passTitle'] = pageTitle

        # Handle timer and redirect logic
        if lastPage == "a":
            session['remainingTime'] -= int(time.time()) - session['lastPageSwitchUnixTime']
            session['lastPageSwitchUnixTime'] = int(time.time())
            session['redirectPage'] = "prac_c1?fid=done"
        elif lastPage == "c3":
            session['lastPageSwitchUnixTime'] = int(time.time())
            session['redirectPage'] = "prac_c1?fid=done"

            # Save c3 answer if provided
            ans_to_save = request.form.get('ans')
            passid_to_save = request.form.get('savepassid')

            if ans_to_save and passid_to_save:
                update_ans_query = """
                    UPDATE tb15_prac_passQop
                    SET c3Ans = ?
                    WHERE sid = ? AND uid = ? AND passID = ?
                """
                cursor.execute(update_ans_query, (ans_to_save, sid, uid, passid_to_save))
                conn.commit()

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return render_template('prac_b.html', passResult=passResult, passOrder=passOrder, nextPassOrder=nextPassOrder)


@app.route('/prac_c1', methods=['GET', 'POST'])
def prac_c1():
    if 'uid' not in session:
        return redirect(url_for('index'))  # Redirect if user is not logged in

    uid = session['uid']
    sid = session.get('sid')
    topID = "01"  # Hardcoded for this example
    conID = "1"   # Hardcoded for this example

    # Get query parameters
    fid = request.args.get('fid')
    action = f"prac_c2?fid={fid}"

    # Save URL and session data
    subtopID = session.get('subtopID')
    passID = session.get('passID')
    pageTitle = f"c1 Prac: {session.get('passTitle')}"

    # Update timer
    session['remainingTime'] -= int(time.time()) - session['lastPageSwitchUnixTime']
    session['lastPageSwitchUnixTime'] = int(time.time())

    return render_template('prac_c1.html', action=action, fid=fid)


@app.route('/prac_c3', methods=['GET', 'POST'])
def prac_c3():
    if 'uid' not in session:
        return redirect(url_for('index'))  # Redirect if user is not logged in

    uid = session['uid']
    sid = session.get('sid')
    topID = "01"  # Hardcoded for this example
    conID = "1"   # Hardcoded for this example

    # Get query parameters
    fid = request.args.get('fid')

    # Determine the action based on fid
    if fid == "same":
        action = f"prac_b?subtop={session.get('subtopID')}&passOrd={session.get('nextPassOrder')}&lastPage=c3"
    elif fid == "back":
        action = f"prac_a?fid=back&subtop={session.get('subtopID')}&lastPage=c3"
    elif fid == "done":
        action = "prac_k2?lastPage=c3"
    else:
        action = ""

    # Save URL and session data
    subtopID = session.get('subtopID')
    passID = session.get('passID')
    pageTitle = f"c3 Prac: {session.get('passTitle')}"

    # Handle form submission
    if request.method == 'POST':
        ans_to_save = request.form.get('ans')
        savepassid = request.form.get('savepassid')

        if ans_to_save and savepassid:
            conn = get_db()
            cursor = conn.cursor()

            try:
                # Update answer in tb15_prac_passQop
                update_ans_query = """
                    UPDATE tb15_prac_passQop
                    SET c2Ans = ?
                    WHERE sid = ? AND uid = ? AND passID = ?
                """
                cursor.execute(update_ans_query, (ans_to_save, sid, uid, savepassid))
                conn.commit()
            except Exception as e:
                print(f"Error saving answer: {e}")
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

    return render_template('prac_c3.html', action=action, fid=fid, passID=passID)


@app.route('/prac_k2', methods=['GET', 'POST'])
def prac_k2():
    if 'uid' not in session:
        return redirect(url_for('index'))  # Redirect if user is not logged in

    uid = session['uid']
    sid = session.get('sid')
    topID = "01"  # Hardcoded for this example

    # Set up action page
    action = "instruction"

    # Fetch topic data
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Fetch topic title
        topic_query = "SELECT * FROM tb12_prac_topic WHERE topID = ?"
        cursor.execute(topic_query, (topID,))
        topic_result = cursor.fetchone()
        topic_title = topic_result['topTitle']

        # Fetch subtopics
        subtop_query = "SELECT * FROM tb13_prac_subtopic WHERE topID = ? ORDER BY subtopID"
        cursor.execute(subtop_query, (topID,))
        subtop_results = cursor.fetchall()

        # Create subtopic string
        subtop_string = ", ".join([subtop['subtopTitle'] for subtop in subtop_results])
        trim_subtop = subtop_string.lstrip(", ")

        # Handle form submission
        last_page = request.args.get('lastPage')
        if last_page == "c3" and request.method == 'POST':
            ans_to_save = request.form.get('ans')
            passid_to_save = request.form.get('savepassid')

            if ans_to_save and passid_to_save:
                update_ans_query = """
                    UPDATE tb15_prac_passQop
                    SET c3Ans = ?
                    WHERE sid = ? AND uid = ? AND passID = ?
                """
                cursor.execute(update_ans_query, (ans_to_save, sid, uid, passid_to_save))
                conn.commit()

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return render_template('prac_k2.html', topic_title=topic_title, trim_subtop=trim_subtop, action=action)

@app.route('/instruction', methods=['GET', 'POST'])
def instruction():
    if 'uid' not in session or 'sid' not in session:
        return redirect(url_for('index'))

    uid = session['uid']
    sid = session['sid']
    topID = "01"  # Assuming fixed topic ID for this example

    # Handle form submission from prac_k2
    if request.method == 'POST':
        ans_to_save = request.form.get('textarea_k2')
        if ans_to_save:
            conn = get_db()
            try:
                cursor = conn.cursor()
                insert_query = """
                    INSERT INTO tb18_prac_topicIdeas (uid, sid, topID, quesID, quesAns)
                    VALUES (?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, (uid, sid, topID, 'prac_k2', ans_to_save))
                conn.commit()
            except Exception as e:
                print(f"Error saving topic ideas: {e}")
                conn.rollback()
            finally:
                conn.close()

    # Set up orders
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute("SELECT * FROM tb1_user WHERE sid = ? AND uid = ?", (sid, uid))
        user_result = cursor.fetchone()

        if user_result:
            # Generate condition order based on UID
            remain = uid % 6
            con_orders = {
                1: "1#2#3#1#2#3#1#2#3#1#2#3#",
                2: "2#3#1#2#3#1#2#3#1#2#3#1#",
                3: "3#1#2#3#1#2#3#1#2#3#1#2#",
                4: "1#3#2#1#3#2#1#3#2#1#3#2#",
                5: "2#1#3#2#1#3#2#1#3#2#1#3#",
                0: "3#2#1#3#2#1#3#2#1#3#2#1#"
            }
            str_domain = "01#"
            str_con = con_orders.get(remain, "1#2#3#1#2#3#1#2#3#1#2#3#")

            # Update user with order information
            update_query = """
                UPDATE tb1_user 
                SET topIDorder = ?, conIDorder = ?
                WHERE sid = ? AND uid = ?
            """
            cursor.execute(update_query, (str_domain, str_con, sid, uid))
            conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

    return render_template('instruction.html')

@app.route('/task_a', methods=['GET', 'POST'])
def task_a():
    # Session validation
    if 'uid' not in session or 'sid' not in session:
        return redirect(url_for('login'))
    
    uid = session['uid']
    sid = session['sid']
    topID = "01"  # Assuming fixed topic ID

    # Debug logging
    app.logger.debug(f'sid: {sid}, uid: {uid}, fid: {request.args.get("fid")}')

    # Handle GET parameters
    fid = request.args.get('fid')
    last_page = request.args.get('lastPage')
    subtop = request.args.get('subtop')

    conn = get_db()
    try:
        cursor = conn.cursor()

        # Handle timer initialization
        if fid in ["begin", "next"]:
            session['startUnixTime'] = int(time.time())
            session['startTimeStamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            session['remainingTime'] = 60  # Debug value
            session['lastPageSwitchUnixTime'] = int(time.time())

            # Insert time record
            cursor.execute("""
                INSERT INTO tb6_taskTime (uid, sid, topID, timeStart, timeStartStamp)
                VALUES (?, ?, ?, ?, ?)
            """, (uid, sid, topID, session['startUnixTime'], session['startTimeStamp']))
            
            # Initialize visited subtopics
            session['visitedSub'] = ""
            visitedSubtop = []

        # Handle back navigation
        if fid == "back":
            session['lastPageSwitchUnixTime'] = int(time.time())
            
            # Update condition
            cursor.execute("""
                UPDATE tb1_user 
                SET conDone = conDone + 1 
                WHERE sid = ? AND uid = ?
            """, (sid, uid))
            
            # Track visited subtopics
            if subtop:
                session['visitedSub'] += subtop
                visitedSubtop = list(session['visitedSub'])

        # Handle answer submission
        if last_page == "c3":
            ans_to_save = request.form.get('ans')
            passid_to_save = request.form.get('savepassid')
            
            if ans_to_save and passid_to_save:
                cursor.execute("""
                    UPDATE tb5_passQop 
                    SET c3Ans = ? 
                    WHERE sid = ? AND uid = ? AND passID = ?
                """, (ans_to_save, sid, uid, passid_to_save))

        # Fetch topic data
        cursor.execute("SELECT * FROM tb2_topic WHERE topID = ?", (topID,))
        topic_result = cursor.fetchone()

        # Fetch subtopics
        cursor.execute("""
            SELECT * FROM tb3_subtopic 
            WHERE topID = ? 
            ORDER BY subtopID
        """, (topID,))
        subtop_results = cursor.fetchall()

        conn.commit()
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Database error: {str(e)}")
        return render_template('error.html'), 500
    finally:
        conn.close()

    # Set redirect page for timer
    session['redirectPage'] = "k2?lastPage=a"

    return render_template(
        'task_a.html',
        topic=topic_result,
        subtopics=subtop_results,
        visitedSubtop=visitedSubtop,
        remainingTime=session.get('remainingTime', 60)
    )

if __name__ == '__main__':
    init_db()  # Initialize database on startup
    app.run(debug=True)