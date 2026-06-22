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

    conn.commit()
    cursor.close()
    conn.close()
    print("Sample data inserted successfully!")

if __name__ == "__main__":
    insert_sample_data()