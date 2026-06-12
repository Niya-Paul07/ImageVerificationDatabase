import os
import psycopg2
import bcrypt
import cv2
import numpy as np
import json

DATABASE_URL = os.environ.get("DATABASE_URL")

def read_photo(path):
    with open(path, "rb") as f:
        return f.read()

def insert_sample_data():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    cursor.execute("""
        INSERT INTO admins (username, password_hash, full_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ("admin", password, "Admin User"))

    students = [
        ("S001", "Aisha Nair", "2003-04-12", "Computer Science", "aisha@email.com", "9876543210", "sample_photos/student1.jpeg"),
        ("S002", "Rahul Menon", "2002-11-05", "Electronics", "rahul@email.com", "9876543211", "sample_photos/student2.jpeg"),
        ("S003", "Priya Suresh", "2003-01-20", "Mechanical", "priya@email.com", "9876543212", "sample_photos/student3.jpeg"),
        ("S004", "Arjun Das", "2002-08-15", "Civil", "arjun@email.com", "9876543213", "sample_photos/student4.jpeg"),
        ("S005", "Meera Pillai", "2003-06-30", "Computer Science", "meera@email.com", "9876543214", "sample_photos/student5.jpeg"),
        ("S006", "Vishnu Kumar", "2002-03-22", "Electronics", "vishnu@email.com", "9876543215", "sample_photos/student6.jpeg"),
        ("S007", "Anjali Raj", "2003-09-10", "Mechanical", "anjali@email.com", "9876543216", "sample_photos/student7.jpeg"),
        ("S008", "Rohan Varma", "2002-12-01", "Civil", "rohan@email.com", "9876543217", "sample_photos/student8.jpeg"),
        ("S009", "Sneha Krishnan", "2003-07-18", "Computer Science", "sneha@email.com", "9876543218", "sample_photos/student9.jpeg"),
        ("S010", "Kiran Thomas", "2002-05-25", "Electronics", "kiran@email.com", "9876543219", "sample_photos/student10.jpeg"),
    ]

    for s in students:
        try:
            photo = read_photo(s[6])
            nparr = np.frombuffer(photo, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            img_resized = cv2.resize(img, (100, 100))
            embedding = json.dumps(img_resized.flatten().tolist())
            cursor.execute("""
                INSERT INTO students (student_id, full_name, dob, department, email, phone, photo, face_embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (student_id) DO NOTHING
            """, (s[0], s[1], s[2], s[3], s[4], s[5], psycopg2.Binary(photo), embedding))
            print(f"Inserted {s[1]}")
        except Exception as e:
            print(f"Error inserting {s[1]}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Sample data inserted successfully!")

if __name__ == "__main__":
    insert_sample_data()