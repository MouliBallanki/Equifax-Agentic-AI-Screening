import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='sails@123',
    database='equifax_screening'
)

cursor = conn.cursor()
cursor.execute("""
    SELECT application_id, first_name, last_name, status, screening_completed, risk_score
    FROM applications
    WHERE first_name='Charles'
    ORDER BY created_at DESC
    LIMIT 1
""")

result = cursor.fetchone()
if result:
    print(f"Application ID: {result[0]}")
    print(f"Name: {result[1]} {result[2]}")
    print(f"Status: {result[3]}")
    print(f"Screening Completed: {result[4]}")
    print(f"Risk Score: {result[5]}")
else:
    print("No application found")

conn.close()
