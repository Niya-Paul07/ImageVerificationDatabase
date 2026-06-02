-- Admin table
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student details table
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    dob DATE NOT NULL,
    department VARCHAR(100),
    email VARCHAR(200) UNIQUE,
    phone VARCHAR(20),
    photo BLOB,
    face_embedding TEXT,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verification logs table
CREATE TABLE IF NOT EXISTS verification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(50) NOT NULL,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result VARCHAR(10) NOT NULL CHECK(result IN ('PASS', 'FAIL')),
    accuracy_percentage FLOAT NOT NULL,
    captured_photo BLOB NOT NULL,
    verified_by VARCHAR(100),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);