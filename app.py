from flask import Flask, request, jsonify, session
import sqlite3
import bcrypt
from sklearn.metrics.pairwise import cosine_similarity
import cv2
import numpy as np
import json
import io
from PIL import Image
from flask import render_template

app = Flask(__name__)
app.secret_key = "cdit_secret_key"

def get_db():
    conn = sqlite3.connect("exam_registration.db")
    conn.row_factory = sqlite3.Row
    return conn

from functools import wraps
from flask import redirect, url_for

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

@app.route("/api/dashboard")
@login_required
def api_dashboard():
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_verifications = conn.execute("SELECT COUNT(*) FROM verification_logs").fetchone()[0]
    total_pass = conn.execute("SELECT COUNT(*) FROM verification_logs WHERE result='PASS'").fetchone()[0]
    total_fail = conn.execute("SELECT COUNT(*) FROM verification_logs WHERE result='FAIL'").fetchone()[0]
    students = conn.execute("SELECT student_id, full_name, department, email, registered_at FROM students ORDER BY registered_at DESC").fetchall()
    recent_verifications = conn.execute("SELECT student_id, result, accuracy_percentage, verified_by, verified_at FROM verification_logs ORDER BY verified_at DESC LIMIT 20").fetchall()
    conn.close()

    return jsonify({
        "total_students": total_students,
        "total_verifications": total_verifications,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "students": [dict(s) for s in students],
        "recent_verifications": [dict(v) for v in recent_verifications]
    })

@app.route("/admin/logout", methods=["POST"])
def logout():
    session.pop("admin", None)
    return jsonify({"message": "Logged out"})

# ── Admin Login ──────────────────────────────────────────
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db()
    admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
    conn.close()

    if admin and bcrypt.checkpw(password.encode(), admin["password_hash"]):
        session["admin"] = username
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

# ── Student Registration ──────────────────────────────────
@app.route("/student/register", methods=["POST"])
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
    try:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        img_resized = cv2.resize(img, (100, 100))
        embedding = json.dumps(img_resized.flatten().tolist())
    except Exception as e:
        return jsonify({"error": "Could not process photo."}), 400

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO students (student_id, full_name, dob, department, email, phone, photo, face_embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, full_name, dob, department, email, phone, img_bytes, embedding))
        conn.commit()
        return jsonify({"message": "Student registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Student ID or email already exists"}), 409
    finally:
        conn.close()

# ── Face Verification ─────────────────────────────────────
@app.route("/verify", methods=["POST"])
def verify_student():
    student_id = request.form.get("student_id")
    photo = request.files.get("photo")
    verified_by = request.form.get("verified_by", "admin")

    if not student_id or not photo:
        return jsonify({"error": "Missing student ID or photo"}), 400

    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()

    if not student:
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    # Load live photo and extract embedding
    img_bytes = photo.read()


    stored_embedding = np.array(json.loads(student["face_embedding"])).reshape(1, -1)
    nparr = np.frombuffer(img_bytes, np.uint8)
    live_img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    live_img_resized = cv2.resize(live_img, (100, 100))
    live_embedding = live_img_resized.flatten().reshape(1, -1)
    similarity = cosine_similarity(stored_embedding, live_embedding)[0][0]
    accuracy_percentage = round(similarity * 100, 2)
    result = "PASS" if accuracy_percentage >= 60 else "FAIL"

    # Log the verification
    conn.execute("""
        INSERT INTO verification_logs (student_id, result, accuracy_percentage, captured_photo, verified_by)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, result, accuracy_percentage, img_bytes, verified_by))
    conn.commit()
    conn.close()

    return jsonify({
        "student_id": student_id,
        "result": result,
        "accuracy_percentage": accuracy_percentage
    })

if __name__ == "__main__":
    app.run(debug=True)