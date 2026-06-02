import sqlite3

def create_database():
    conn = sqlite3.connect("exam_registration.db")
    cursor = conn.cursor()
    
    # Read and execute the schema file
    with open("schema.sql", "r") as f:
        schema = f.read()
    
    cursor.executescript(schema)
    conn.commit()
    conn.close()
    print("Database created successfully!")

if __name__ == "__main__":
    create_database()