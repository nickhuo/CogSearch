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

            return redirect(url_for('practice_instruction'))

        except (BadRequestKeyError, ValueError, KeyError) as e:
            error = "Please fill all required fields correctly"
            db.rollback()
        except sqlite3.Error as e:
            error = f"Database error: {str(e)}"
            db.rollback()

    return render_template('demographic.html', error=error)

@app.route('/practice-instruction')
def practice_instruction():
    return render_template('practice_instruction.html')

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



if __name__ == '__main__':
    init_db()  # Initialize database on startup
    app.run(debug=True)