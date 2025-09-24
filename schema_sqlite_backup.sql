-- Create all tables with SQLite compatible syntax
PRAGMA foreign_keys = OFF;

-- output1_url
CREATE TABLE IF NOT EXISTS output1_url (
    op1ID INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    passID TEXT NOT NULL CHECK (LENGTH(passID) = 6),
    pageTypeID TEXT NOT NULL,
    time_stamp TEXT NOT NULL,
    unixTime INTEGER NOT NULL,
    time_interval INTEGER NOT NULL,
    url TEXT NOT NULL,
    pageTitle TEXT NOT NULL
);

-- tb1_user
CREATE TABLE IF NOT EXISTS tb1_user (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    sid TEXT NOT NULL,
    topIDorder TEXT,
    subtopIDorder TEXT NOT NULL,
    conIDorder TEXT NOT NULL,
    taskDone INTEGER NOT NULL,
    conDone INTEGER NOT NULL,
    signedConsent TEXT NOT NULL,
    signedDate TEXT NOT NULL
);

-- tb2_topic
CREATE TABLE IF NOT EXISTS tb2_topic (
    topID TEXT PRIMARY KEY,
    topTitle TEXT NOT NULL,
    topIdeasBonusWords TEXT NOT NULL
);

-- tb3_subtopic
CREATE TABLE IF NOT EXISTS tb3_subtopic (
    subtopID TEXT NOT NULL,
    topID TEXT NOT NULL,
    subtopTitle TEXT NOT NULL,
    subtopQuesOne TEXT NOT NULL,
    subtopAnsOne TEXT NOT NULL,
    subtopQuesTwo TEXT NOT NULL,
    subtopAnsTwo TEXT NOT NULL,
    subtopQuesThr TEXT NOT NULL,
    subtopAnsThr TEXT NOT NULL,
    PRIMARY KEY (subtopID, topID)
);

-- tb4_passage
CREATE TABLE IF NOT EXISTS tb4_passage (
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    passID TEXT NOT NULL CHECK (LENGTH(passID) = 6),
    passOrder TEXT NOT NULL,
    passTitle TEXT NOT NULL,
    passText TEXT NOT NULL,
    PRIMARY KEY (topID, subtopID, conID, passID)
);

-- tb5_passQop
CREATE TABLE IF NOT EXISTS tb5_passQop (
    tb5id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    passID TEXT NOT NULL CHECK (LENGTH(passID) = 6),
    passOrder TEXT NOT NULL,
    c1Ans INTEGER NOT NULL,
    c2Ans INTEGER NOT NULL DEFAULT 0,
    c3Ans INTEGER NOT NULL DEFAULT 0,
    passRT INTEGER NOT NULL DEFAULT 0
);

-- tb6_taskTime
CREATE TABLE IF NOT EXISTS tb6_taskTime (
    tb6id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    timeStart INTEGER NOT NULL,
    timeEnd INTEGER NOT NULL,
    timeStartStamp TEXT NOT NULL,
    timeEndStamp TEXT NOT NULL
);

-- tb7_topicSummary
CREATE TABLE IF NOT EXISTS tb7_topicSummary (
    tb7id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    quesID TEXT NOT NULL,
    quesAns TEXT NOT NULL
);

-- tb8_topicIdeas
CREATE TABLE IF NOT EXISTS tb8_topicIdeas (
    tb8id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    quesID TEXT NOT NULL,
    quesAns TEXT NOT NULL
);

-- tb9_topicBonus
CREATE TABLE IF NOT EXISTS tb9_topicBonus (
    tb9id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    quesID TEXT NOT NULL,
    quesAns TEXT NOT NULL,
    bonusWord TEXT NOT NULL,
    bonusWordCnt INTEGER DEFAULT 0,
    bonusMoney REAL DEFAULT 0.00
);

-- tb10_subtopQos
CREATE TABLE IF NOT EXISTS tb10_subtopQos (
    tb10id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    pageTypeID TEXT NOT NULL,
    quesAns1 TEXT NOT NULL,
    quesAns2 TEXT NOT NULL,
    quesAns3 TEXT NOT NULL,
    subtopScore REAL NOT NULL
);

-- tb11_profile
CREATE TABLE IF NOT EXISTS tb11_profile (
    tb11id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    dobMonth TEXT NOT NULL,
    dobDay TEXT NOT NULL,
    dobYear TEXT NOT NULL,
    dobSum TEXT NOT NULL,
    age TEXT NOT NULL,
    gender TEXT NOT NULL,
    edu TEXT NOT NULL,
    natEng TEXT NOT NULL,
    firLan TEXT NOT NULL,
    ageEng TEXT NOT NULL,
    hisLat TEXT NOT NULL,
    race TEXT NOT NULL,
    lc1 TEXT DEFAULT '',
    lc2 TEXT DEFAULT '',
    lc3 TEXT DEFAULT '',
    lc4 TEXT DEFAULT '',
    lc5 TEXT DEFAULT '',
    lc6 TEXT DEFAULT '',
    lc7 TEXT DEFAULT '',
    lc8 TEXT DEFAULT '',
    lc9 TEXT DEFAULT '',
    lc10 TEXT DEFAULT '',
    lcOneScore REAL DEFAULT 0.0,
    lcOneRT INTEGER DEFAULT 0,
    lc11 TEXT DEFAULT '',
    lc12 TEXT DEFAULT '',
    lc13 TEXT DEFAULT '',
    lc14 TEXT DEFAULT '',
    lc15 TEXT DEFAULT '',
    lc16 TEXT DEFAULT '',
    lc17 TEXT DEFAULT '',
    lc18 TEXT DEFAULT '',
    lc19 TEXT DEFAULT '',
    lc20 TEXT DEFAULT '',
    lcTwoScore REAL DEFAULT 0.0,
    lcTwoRT INTEGER DEFAULT 0,
    voc1 TEXT DEFAULT '',
    voc2 TEXT DEFAULT '',
    voc3 TEXT DEFAULT '',
    voc4 TEXT DEFAULT '',
    voc5 TEXT DEFAULT '',
    voc6 TEXT DEFAULT '',
    voc7 TEXT DEFAULT '',
    voc8 TEXT DEFAULT '',
    voc9 TEXT DEFAULT '',
    voc10 TEXT DEFAULT '',
    voc11 TEXT DEFAULT '',
    voc12 TEXT DEFAULT '',
    voc13 TEXT DEFAULT '',
    voc14 TEXT DEFAULT '',
    voc15 TEXT DEFAULT '',
    vocScore REAL DEFAULT 0.0
);

-- tb12_prac_topic to tb22_multiQop follow similar patterns

-- tb12_prac_topic
CREATE TABLE IF NOT EXISTS tb12_prac_topic (
    topID TEXT PRIMARY KEY,
    topTitle TEXT NOT NULL,
    topIdeasBonusWords TEXT NOT NULL
);

-- tb13_prac_subtopic
CREATE TABLE IF NOT EXISTS tb13_prac_subtopic (
    subtopID TEXT NOT NULL,
    topID TEXT NOT NULL,
    subtopTitle TEXT NOT NULL,
    subtopQuesOne TEXT NOT NULL,
    subtopAnsOne TEXT NOT NULL,
    subtopQuesTwo TEXT NOT NULL,
    subtopAnsTwo TEXT NOT NULL,
    subtopQuesThr TEXT NOT NULL,
    subtopAnsThr TEXT NOT NULL,
    PRIMARY KEY (subtopID, topID)
);

-- tb14_prac_passage
CREATE TABLE IF NOT EXISTS tb14_prac_passage (
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    passID TEXT NOT NULL CHECK (LENGTH(passID) = 6),
    passOrder TEXT NOT NULL,
    passTitle TEXT NOT NULL,
    passText TEXT NOT NULL,
    PRIMARY KEY (topID, subtopID, conID, passID)
);

-- tb15_prac_passQop
CREATE TABLE IF NOT EXISTS tb15_prac_passQop (
    tb15id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    passID TEXT NOT NULL CHECK (LENGTH(passID) = 6),
    passOrder TEXT NOT NULL,
    c1Ans INTEGER NOT NULL,
    c2Ans INTEGER NOT NULL,
    c3Ans INTEGER NOT NULL,
    passRT INTEGER NOT NULL
);

-- tb16_prac_taskTime
CREATE TABLE IF NOT EXISTS tb16_prac_taskTime (
    tb16id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    timeStart INTEGER NOT NULL,
    timeEnd INTEGER NOT NULL,
    timeStartStamp TEXT NOT NULL,
    timeEndStamp TEXT NOT NULL
);

-- tb17_prac_topicSummary
CREATE TABLE IF NOT EXISTS tb17_prac_topicSummary (
    tb17id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    quesID TEXT NOT NULL,
    quesAns TEXT NOT NULL
);

-- tb18_prac_topicIdeas
CREATE TABLE IF NOT EXISTS tb18_prac_topicIdeas (
    tb18id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    quesID TEXT NOT NULL,
    quesAns TEXT NOT NULL
);

-- tb19_prac_topicBonus
CREATE TABLE IF NOT EXISTS tb19_prac_topicBonus (
    tb19id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    quesID TEXT NOT NULL,
    quesAns TEXT NOT NULL,
    bonusWord TEXT NOT NULL,
    bonusWordCnt INTEGER DEFAULT 0,
    bonusMoney REAL DEFAULT 0.00
);

-- tb20_prac_subtopQos
CREATE TABLE IF NOT EXISTS tb20_prac_subtopQos (
    tb20id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    pageTypeID TEXT NOT NULL,
    quesAns1 TEXT NOT NULL,
    quesAns2 TEXT NOT NULL,
    quesAns3 TEXT NOT NULL,
    subtopScore REAL NOT NULL
);

-- Example for tb21_questions
CREATE TABLE IF NOT EXISTS tb21_questions (
    questionID TEXT PRIMARY KEY,
    passID TEXT NOT NULL CHECK (LENGTH(passID) = 6),
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    passOrder TEXT NOT NULL,
    passTitle TEXT NOT NULL,
    questionText TEXT NOT NULL,
    choiceA TEXT NOT NULL,
    choiceB TEXT NOT NULL,
    choiceC TEXT NOT NULL,
    choiceD TEXT NOT NULL,
    correctAns TEXT NOT NULL
);

-- tb22_multiQop
CREATE TABLE IF NOT EXISTS tb22_multiQop (
    tb22id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    questionID TEXT NOT NULL,
    topID TEXT NOT NULL,
    subtopID TEXT NOT NULL,
    conID TEXT NOT NULL,
    passID TEXT NOT NULL CHECK (LENGTH(passID) = 6),
    passOrder TEXT NOT NULL,
    choice TEXT NOT NULL,
    isCorrect INTEGER NOT NULL
);

-- tb27_letter_item
CREATE TABLE IF NOT EXISTS tb27_letter_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    sid TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    item_index INTEGER NOT NULL,
    left_str TEXT NOT NULL,
    right_str TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    response TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    reaction_time_ms INTEGER NOT NULL,
    inter_question_interval_ms INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

PRAGMA foreign_keys = ON;
