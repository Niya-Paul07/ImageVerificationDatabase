import sqlite3
import bcrypt

def read_photo(path):
    with open(path, "rb") as f:
        return f.read()

def insert_sample_data():
    conn = sqlite3.connect("exam_registration.db")
    cursor = conn.cursor()

    # Sample admin
    password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
    cursor.execute("""
        INSERT OR IGNORE INTO admins (username, password_hash, full_name)
        VALUES (?, ?, ?)
    """, ("admin", password, "Admin User"))

    # Sample students
    students = [
        ("S001", "Aisha Nair", "2003-04-12", "Computer Science", "aisha@email.com", "9876543210", "sample_photos/student1.jpg"),
        ("S002", "Rahul Menon", "2002-11-05", "Electronics", "rahul@email.com", "9876543211", "sample_photos/student2.jpg"),
        ("S003", "Priya Suresh", "2003-01-20", "Mechanical", "priya@email.com", "9876543212", "sample_photos/student3.jpg"),
        ("S004", "Arjun Das", "2002-08-15", "Civil", "arjun@email.com", "9876543213", "sample_photos/student4.jpg"),
        ("S005", "Meera Pillai", "2003-06-30", "Computer Science", "meera@email.com", "9876543214", "sample_photos/student5.jpg"),
        ("S006", "Vishnu Kumar", "2002-03-22", "Electronics", "vishnu@email.com", "9876543215", "sample_photos/student6.jpg"),
        ("S007", "Anjali Raj", "2003-09-10", "Mechanical", "anjali@email.com", "9876543216", "sample_photos/student7.jpg"),
        ("S008", "Rohan Varma", "2002-12-01", "Civil", "rohan@email.com", "9876543217", "sample_photos/student8.jpg"),
        ("S009", "Sneha Krishnan", "2003-07-18", "Computer Science", "sneha@email.com", "9876543218", "sample_photos/student9.jpg"),
        ("S010", "Kiran Thomas", "2002-05-25", "Electronics", "kiran@email.com", "9876543219", "sample_photos/student10.jpg"),
    ]

    for s in students:
        photo = read_photo(s[6])
        cursor.execute("""
            INSERT OR IGNORE INTO students 
            (student_id, full_name, dob, department, email, phone, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (s[0], s[1], s[2], s[3], s[4], s[5], photo))

    conn.commit()
    conn.close()
    print("Sample data inserted successfully!")

if __name__ == "__main__":
    insert_sample_data()