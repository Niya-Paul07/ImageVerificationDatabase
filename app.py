
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
import os
import psycopg2
import psycopg2.extras
import bcrypt
import boto3
import json
from PIL import Image
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cdit_secret_key")

@app.after_request
def add_no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

def get_db():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"), cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            student_id VARCHAR(50) UNIQUE NOT NULL,
            full_name VARCHAR(200) NOT NULL,
            dob DATE NOT NULL,
            department VARCHAR(100),
            email VARCHAR(200) UNIQUE,
            phone VARCHAR(20),
            photo BYTEA,
            face_embedding TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_logs (
            id SERIAL PRIMARY KEY,
            student_id VARCHAR(50) NOT NULL,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result VARCHAR(10) NOT NULL,
            accuracy_percentage FLOAT,
            captured_photo BYTEA,
            verified_by VARCHAR(100)
        )
    """)
    # Create default admin if not exists
    password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    cursor.execute("""
        INSERT INTO admins (username, password_hash, full_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ("admin", password, "Admin User"))
    conn.commit()
    cursor.close()
    conn.close()

with app.app_context():
    init_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

# ── Pages ─────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("login.html")

@app.route("/register")
@login_required
def register():
    return render_template("register.html")

@app.route("/verify-page")
@login_required
def verify_page():
    return render_template("verify.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html")

# ── Admin Login ───────────────────────────────────────────
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if admin and bcrypt.checkpw(password.encode(), admin["password_hash"].encode()):
        session["admin"] = username
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

# ── Admin Logout ──────────────────────────────────────────
@app.route("/admin/logout", methods=["POST"])
def logout():
    session.pop("admin", None)
    return jsonify({"message": "Logged out"})

# ── Student Registration ──────────────────────────────────
@app.route("/student/register", methods=["POST"])
@login_required
def register_student():
    student_id = request.form.get("student_id")
    full_name = request.form.get("full_name")
    dob = request.form.get("dob")
    department = request.form.get("department")
    email = request.form.get("email")
    phone = request.form.get("phone")
    photo = request.files.get("photo")

    if not all([student_id, full_name, dob, photo]):
        return jsonify({"error": "Missing required fields"}), 400

    img_bytes = photo.read()
    embedding = "rekognition"

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO students (student_id, full_name, dob, department, email, phone, photo, face_embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (student_id, full_name, dob, department, email, phone, psycopg2.Binary(img_bytes), embedding))
        conn.commit()
        return jsonify({"message": "Student registered successfully"})
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": "Student ID or email already exists"}), 409
    finally:
        cursor.close()
        conn.close()

# ── Face Verification ─────────────────────────────────────
@app.route("/verify", methods=["POST"])
@login_required
def verify_student():
    student_id = request.form.get("student_id")
    photo = request.files.get("photo")
    verified_by = request.form.get("verified_by", "admin")

    if not student_id or not photo:
        return jsonify({"error": "Missing student ID or photo"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    img_bytes = photo.read()

    try:
        rekognition = boto3.client('rekognition', region_name='us-east-1')
        source_bytes = bytes(student["photo"]) if isinstance(student["photo"], memoryview) else student["photo"]
        response = rekognition.compare_faces(
            SourceImage={'Bytes': source_bytes},
            TargetImage={'Bytes': img_bytes},
            SimilarityThreshold=60
        )
        if response['FaceMatches']:
            accuracy_percentage = round(response['FaceMatches'][0]['Similarity'], 2)
            result = "PASS"
        else:
            accuracy_percentage = 0.0
            result = "FAIL"
    except Exception as e:
        cursor.close()
        conn.close()
        error_msg = str(e)
        if 'InvalidImageFormat' in error_msg or 'InvalidParameter' in error_msg or 'no face' in error_msg.lower() or 'Face' in error_msg:
            return jsonify({"error": "No face detected in the captured photo. Please upload a clear front-facing photo."}), 400
        return jsonify({"error": f"Face comparison failed: {error_msg}"}), 500

    cursor.execute("""
        INSERT INTO verification_logs (student_id, result, accuracy_percentage, captured_photo, verified_by)
        VALUES (%s, %s, %s, %s, %s)
    """, (student_id, result, accuracy_percentage, psycopg2.Binary(img_bytes), verified_by))
    conn.commit()
    cursor.close()
    conn.close()

    import base64
    registered_photo_b64 = base64.b64encode(bytes(student["photo"])).decode("utf-8")
    captured_photo_b64 = base64.b64encode(img_bytes).decode("utf-8")

    return jsonify({
        "student_id": student_id,
        "result": result,
        "accuracy_percentage": accuracy_percentage,
        "registered_photo": registered_photo_b64,
        "captured_photo": captured_photo_b64
    })

# ── Dashboard API ─────────────────────────────────────────
@app.route("/api/dashboard")
@login_required
def api_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM students")
    total_students = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(DISTINCT student_id) as count FROM verification_logs")
    total_verifications = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(DISTINCT student_id) as count FROM verification_logs WHERE result='PASS'")
    total_pass = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(DISTINCT student_id) as count FROM verification_logs WHERE result='FAIL'")
    total_fail = cursor.fetchone()["count"]
    cursor.execute("SELECT student_id, full_name, department, email, registered_at FROM students ORDER BY registered_at DESC")
    students = cursor.fetchall()
    cursor.execute("SELECT student_id, result, accuracy_percentage, verified_by, verified_at FROM verification_logs ORDER BY verified_at DESC LIMIT 20")
    recent_verifications = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({
        "total_students": total_students,
        "total_verifications": total_verifications,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "students": [dict(s) for s in students],
        "recent_verifications": [dict(v) for v in recent_verifications]
    })

@app.route("/api/student/<student_id>")
@login_required
def get_student(student_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, full_name, dob, department, email FROM students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(dict(student))


@app.route("/student/photo/<student_id>")
@login_required
def student_photo(student_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT photo FROM students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    if not student or not student["photo"]:
        return "", 404
    from flask import Response
    photo_bytes = bytes(student["photo"]) if isinstance(student["photo"], memoryview) else student["photo"]
    return Response(photo_bytes, mimetype="image/jpeg")

@app.route("/api/check-session")
def check_session():
    return jsonify({"logged_in": "admin" in session})

if __name__ == "__main__":
    app.run(debug=True)
