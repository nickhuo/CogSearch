# Flask Web Application Documentation

## Overview

This Flask web application implements a cognitive experiment workflow. It manages user registration, consent, demographic data collection, practice and main experimental tasks, vocabulary and letter comparison tests, answer submissions, and detailed logging. MySQL is used as the backend database.

---

## 1. Project Structure

- **Main Application File:** `app.py`
- **Templates Directory:** `/templates`  
  Contains all HTML templates (e.g., `index.html`, `task_a.html`, etc.)
- **Static Files Directory:** `/static`  
  Stores JavaScript, CSS, and image assets.
- **Database Utility File:** `db_utils.py`  
  Encapsulates database connection logic and utility functions such as `save_url()`.

---

## 2. Configuration

- Uses the `SECRET_KEY` environment variable (defaults to `'dev-secret-key'` if unset).
- Database configuration (hardcoded in app):
  ```python
  app.config['MYSQL_HOST'] = 'localhost'
  app.config['MYSQL_USER'] = 'root'
  app.config['MYSQL_PASSWORD'] = 'root'
  app.config['MYSQL_DB'] = 'cogsearch_textsearch3'
  ```

---

## 3. Session Variables

Session variables are used extensively for state management across requests. Common keys include:

- `uid`, `sid`: User/session identifiers
- `topID`, `subtopID`, `conID`, `passID`, `passOrder`, `nextPassOrder`
- `visitedSub`, `passTitle`
- `startUnixTime`, `remainingTime`, `redirectPage`

---

## 4. Key Functional Routes

- `/`: Landing page
- `/consent`: Clears session and loads the consent form
- `/demographic`: Handles initial profile creation and demographic data storage
- `/prac_*`: Handles practice task routes
- `/task_*`: Main experimental task flow (reading passages, answering questions)
- `/vocab`, `/let_comp_one`, `/let_comp_two`: Vocabulary and letter comparison tests
- `/done`: Final evaluation, score computation, bonus logic, and session cleanup

---

## 5. Important Functions & Utilities

- `get_db_connection()`: Opens a MySQL connection
- `get_time_stamp_cdt()`: Returns the current timestamp in UTC-5 (Central Daylight Time)
- `save_url(...)`: Logs each page visit and interaction (defined in `db_utils.py`)
- `save_pass_answer(qid, ans_to_save, table)`: Centralized answer submission for comprehension questions
- `format_pass_id(...)`: Constructs a 6-digit identifier using `subtopID`, `conID`, and `passOrder`

---

## 6. Database Tables

- `tb1_user`: Stores user metadata
- `tb11_profile`: Stores demographics, vocabulary, and comparison results
- `tb5_passQop`, `tb15_prac_passQop`: Store answers to comprehension questions
- `tb21_questions`, `tb22_multiQop`: Store multi-choice questions and responses
- `output1_url`: Stores page access logs with timestamps for each user
- `tb2_topic`, `tb3_subtopic`, etc.: Store passage metadata and content

---

## 7. Data Logging & Timing

The application tracks time per page, per passage, and for letter comparison/vocabulary tasks. Timing data is extracted from `output1_url` and later backfilled into the relevant tables.

---

## 8. Score Computation

- **Vocabulary:**  
  +1 per correct answer, -0.2 per incorrect answer, 0 for "unsure" (choice = "6")
- **Letter Comparison:**  
  +1 per correct answer; no penalty for incorrect answers
- **Bonus Words:**  
  Matched from user's topic ideas against `topIdeasBonusWords`

---

## 9. Templates

Key templates for front-end rendering include:

- `consent.html`, `demographic.html`, `timer.html`
- `prac_a.html`, `prac_b.html`, `prac_c1.html` to `prac_c3.html`
- `task_a.html`, `task_b.html`, `task_c1.html` to `task_c4.html`
- `let_comp_one.html`, `let_comp_two.html`
- `vocab.html`, `done.html`

---

## 10. Debugging Tips

- All exceptions are printed to the server logs (using `print(...)` statements)
- Flask runs with `debug=True` by default
- SQL errors, timeouts, or session mismanagement will print traceable messages to the logs
