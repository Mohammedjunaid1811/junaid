import psycopg2

def get_connection():
    conn = psycopg2.connect(
        database="student_risk_db",
        user="postgres",
        password="18112005itachi$MJ",
        host="localhost",
        port="5432"
    )
    return conn