import sqlite3
import bcrypt

conn = sqlite3.connect("exam_registration.db")
cursor = conn.cursor()
password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
cursor.execute("INSERT OR IGNORE INTO admins (username, password_hash, full_name) VALUES (?, ?, ?)", 
               ("admin", password, "Admin User"))
conn.commit()
conn.close()
print("Done")