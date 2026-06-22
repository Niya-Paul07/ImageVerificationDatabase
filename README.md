# Exam Registration Platform

> A web-based exam candidate registration and identity verification system built for **C-DIT, Trivandrum**.

---

## Overview

The Exam Registration Platform allows administrators to register exam candidates and verify their identity on exam day using automated face recognition powered by AWS Rekognition.

**Core workflows:**
- **Student Data** — Candidate details and photos are preloaded into the system by the administrator; no on-site registration needed.
- **Verify Student** — Invigilator enters the Student ID, confirms candidate details, and captures a live photo via webcam; AWS Rekognition compares it against the registered photo and returns a PASS or FAIL result.

## Screenshots
### Login Page
![Login Page](screenshots/Loginpage.jpeg)

### Dashboard
![Dashboard](screenshots/Dashboardpage.jpeg)

### Verification of students
![Verifystudents](screenshots/Verificationpage.jpeg)

### Registration of students
![Reg.ofstudents](screenshots/Reportspage.jpeg)

# Features

- Secure admin login with bcrypt password hashing
- Dashboard with live stats — total registered students, passed/failed verifications, total checks (counted uniquely per student based on latest result)
- Student data predefined and loaded into the system (no manual registration needed)
- Automated face verification using AWS Rekognition (CompareFaces API)
- Step-by-step verification flow — enter ID, confirm student details, auto-open webcam, capture with Enter key
- Displays both registered and captured photos side by side after verification
- Verification result shown as popup — PASS or FAIL with accuracy percentage
- Auto-advances to next candidate — 15 seconds on PASS, 5 seconds on FAIL
- Search registered students by name or Student ID
- Recent verification log with accuracy percentages
- Reports page — view registered students, passed and failed verifications (admin access only)
- Persistent sidebar with Dashboard, Verify, Report, Logout — always visible across all pages
- Full session-based auth — back/forward browser navigation blocked after logout
- Student ID strictly validated — only S + 3 digits format allowed (e.g. S001), special characters blocked
---

## Tech Stack

| Layer         | Technology                                |
|-----------------------------------------------------------|        
| Frontend      | HTML / CSS / JavaScript                   |
| Backend       | Python/Flask                              |
| Database      | PostgreSQL (hosted on Render)             |
| Auth          | bcrypt (password hashing)                 |
| Face AI       | AWS Rekognition (CompareFaces)            |
| Deployment    | Render (free tier web service)            |


---

## Prerequisites

- Python 3.9.13
- Flask 3.0
- PostgreSQL 15
- AWS account with Rekognition access
- OpenCV 4.11
- NumPy 2.0
- VS Code

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Niya-Paul07/ImageVerificationDatabase.git
cd ImageVerificationDatabase

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create a .env file in the project root
#    In your terminal (inside the project folder):
#
#    Windows:
#      type nul > .env
#
#    Mac/Linux:
#      touch .env
#
#    Then open .env in VS Code and add the variables below.
```
Add the following to your `.env` file:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/YOUR_DB_NAME
SECRET_KEY=your_secret_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
```

```bash
# 4. Start the app
flask run
```
Open `http://localhost:5000` in your browser.

---

## Default Admin Credentials

| Username | Password  |
|----------|-----------|
| `admin`  | `admin123` |

> ⚠️ Change the default password before deploying to production.

---
## AWS Rekognition Setup

1. Log in to the [AWS Console](https://console.aws.amazon.com/).
2. Go to **IAM** → Create a new user with **AmazonRekognitionReadOnlyAccess** (or FullAccess).
3. Generate **Access Key ID** and **Secret Access Key** for that user.
4. Add them to your `.env` file as shown above.
5. Make sure your AWS region matches the region where Rekognition is available (e.g. `us-east-1`).

No S3 bucket is needed — photos are stored directly as binary data (`BYTEA`) in PostgreSQL.

---

## Usage

### Admin Login
- Navigate to the login page.
- Enter your username and password.
- Default credentials — username: `admin` | password: `admin123`
- Change the password after first login.

### Verifying a Student on Exam Day
1. Go to **Verify** from the sidebar.
2. Enter the Student ID (format: S001 — only letters and digits allowed).
3. Press Enter — candidate details are shown for confirmation.
4. Press Enter again — webcam opens automatically.
5. Press Enter to capture the live photo.
6. Both registered and captured photos are shown side by side.
7. Result popup shows **PASS** or **FAIL** with accuracy percentage.
8. Screen auto-advances to the next candidate after the timer expires (15s on PASS, 5s on FAIL).

---


## Project Structure

```
ImageVerificationDatabase/
├── sample_photos/
├── screenshots/             # Main application entry point
├── templates/               # HTML pages
│   ├── login.html
│   ├── dashboard.html
│   ├── register.html
│   └── verify.html
├── .gitignore            
├── app.py                   # Main application file
├── build.sh                 # Deployment build script
├── database.py              # Creates the database from schema.sql
├── schema.sql               # SQL schema — table definitions
├── create_admin.py          # Script to initialise admin account
├── exam_registration.db     # SQLite database (auto-created)
├── insert_sample_data.py    # stores sampledata and inserts into app   
├── requirements.txt         # Lists required Python packages
├── runtime.txt              # Specifies Python-runtime version
├── Procfile                 # Deployment configuration file       
├── static/                  # CSS, JS, images
└── README.md                # Project documentation
```

---
## Database

PostgreSQL is used for all data storage, hosted on **Render's free tier**.

- Student photos are stored as `BYTEA` directly in the database — no external file storage needed.
- Face embeddings are not stored; AWS Rekognition performs live comparison on each verification request.

To reset the database locally:

```bash
python database.py
python create_admin.py
```

---

## Deployment (Render)

1. Push your code to GitHub.
2. Go to [Render](https://render.com) and create a new **Web Service**.
3. Connect your GitHub repository.
4. Set the following environment variables in Render's dashboard:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
5. Set the start command to:
   ```
   gunicorn app:app
   ```
6. Deploy.

---

## Known Limitations

- Single admin account (no multi-user roles yet).
- AWS Rekognition requires a clear, front-facing photo for accurate results.
- Render free tier spins down after inactivity — first request may be slow.
- Student data is preloaded by the administrator; students cannot self-register.
- Student ID must follow the format S001 (S + 3 digits) — no special characters allowed.
- Webcam access required for verification; upload fallback not available.

---

## License

This project is licensed under the MIT License.

