
DROP TABLE IF EXISTS tb1_user;

CREATE TABLE IF NOT EXISTS tb1_user (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    sid INTEGER NOT NULL,
    mturk_id TEXT NOT NULL,
    consent_time DATETIME NOT NULL,
    dob_month INTEGER,
    dob_day INTEGER,
    dob_year INTEGER,
    age INTEGER,
    gender INTEGER,
    education REAL,
    is_native_english BOOLEAN,
    first_language TEXT,
    english_acquisition_age INTEGER,
    is_hispanic_latino BOOLEAN,
    race INTEGER,
    taskDone INTEGER DEFAULT 0,
    conDone INTEGER DEFAULT 0,
    signedConsent BOOLEAN DEFAULT FALSE,
    signedDate DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);