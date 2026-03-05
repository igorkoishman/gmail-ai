import pandas as pd
from database_engine import DatabaseEngine

db = DatabaseEngine()
conn = db._get_connection()

df = pd.read_sql("SELECT sender, subject, snippet FROM emails WHERE manual_category = 'Marina' LIMIT 20", conn)
print("Manual Marina labels:")
print(df.to_string())
conn.close()
