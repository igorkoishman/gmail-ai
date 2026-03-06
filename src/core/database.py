import mysql.connector
import os
from typing import List, Dict, Any, Optional
from .config import Config

class DatabaseEngine:
    def __init__(self):
        # Using Docker environment variables from your docker-compose.yml
        self.config = {
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'host': os.getenv('DB_HOST', '127.0.0.1'),
            'database': os.getenv('DB_NAME', 'gmail'),
            'port': os.getenv('DB_PORT', '3306')
        }
        self._init_db()

    def _get_connection(self):
        return mysql.connector.connect(**self.config)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Increase column width if it already exists
        try:
            cursor.execute("ALTER TABLE emails MODIFY COLUMN threadId VARCHAR(255)")
            cursor.execute("ALTER TABLE emails MODIFY COLUMN date DATETIME")
            print("DB Schema: Upgraded columns to required types (threadId: VARCHAR(255), date: DATETIME).")
        except mysql.connector.Error:
            # This will fail if the table doesn't exist, which is fine.
            # It might also fail if the column is already the right size, also fine.
            pass

        # Create table for emails with the correct size
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INT AUTO_INCREMENT PRIMARY KEY,
                threadId VARCHAR(255) UNIQUE,
                sender VARCHAR(255),
                subject VARCHAR(512),
                date DATETIME,
                snippet TEXT,
                full_text LONGTEXT,
                raw_body LONGTEXT,
                ai_category VARCHAR(100),
                ai_confidence FLOAT,
                manual_category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        # Create table for distributed locks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locks (
                lock_name VARCHAR(100) PRIMARY KEY,
                locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add indexes for performance on category lookups
        try:
            cursor.execute("CREATE INDEX idx_manual_category ON emails (manual_category)")
            cursor.execute("CREATE INDEX idx_ai_category ON emails (ai_category)")
            cursor.execute("CREATE INDEX idx_manual_ai_category ON emails (manual_category, ai_category)")
            print("DB Schema: Added indexes for category columns.")
        except mysql.connector.Error as err:
            if err.errno == 1061: # Duplicate key name (index already exists)
                print("DB Schema: Indexes already exist, skipping creation.")
            else:
                print(f"DB Schema: Error adding indexes: {err}")
        conn.commit()
        cursor.close()
        conn.close()

    def acquire_lock(self, lock_name: str, expire_minutes: int = 10) -> bool:
        """Try to acquire a named lock. Returns True if successful."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Clean up expired locks first (Safety)
            cursor.execute("DELETE FROM locks WHERE locked_at < NOW() - INTERVAL %s MINUTE", (expire_minutes,))
            
            # Try to insert the lock
            cursor.execute("INSERT INTO locks (lock_name) VALUES (%s)", (lock_name,))
            conn.commit()
            return True
        except mysql.connector.IntegrityError:
            # Lock already exists
            return False
        finally:
            cursor.close()
            conn.close()

    def release_lock(self, lock_name: str):
        """Release a named lock."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM locks WHERE lock_name = %s", (lock_name,))
        conn.commit()
        cursor.close()
        conn.close()

    def save_emails(self, emails_data: List[Dict[str, Any]]):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = """
            INSERT INTO emails (threadId, sender, subject, date, snippet, full_text, raw_body)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                sender = VALUES(sender),
                subject = VALUES(subject),
                date = VALUES(date),
                snippet = VALUES(snippet),
                full_text = VALUES(full_text),
                raw_body = VALUES(raw_body)
        """
        
        for e in emails_data:
            cursor.execute(sql, (
                e['threadId'], e['sender'], e['subject'], e['date'], 
                e['snippet'], e['full_text'], e['raw_body']
            ))
            
        conn.commit()
        cursor.close()
        conn.close()

    def get_emails_for_ai(self, limit: int = 200, reclassify_ai_labels: bool = False) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM emails WHERE manual_category IS NULL"
        if not reclassify_ai_labels:
            query += " AND ai_category IS NULL"
        query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return rows

    def update_ai_predictions(self, results: List[Dict[str, Any]]):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = "UPDATE emails SET ai_category = %s, ai_confidence = %s WHERE threadId = %s"
        
        for r in results:
            cursor.execute(sql, (r['category'], r['confidence'], r['threadId']))
            
        conn.commit()
        cursor.close()
        conn.close()

    def get_ai_classified_count(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        # Count emails that have been AI-classified but not manually overridden
        query = "SELECT COUNT(*) FROM emails WHERE ai_category IS NOT NULL AND manual_category IS NULL"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    def get_training_data(self) -> List[Dict[str, Any]]:
        """Fetch all emails with manual labels first, then fallback to AI labels."""
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Prioritize manual_category (your word is the truth)
        query = """
            SELECT full_text, COALESCE(manual_category, ai_category) as category 
            FROM emails 
            WHERE manual_category IS NOT NULL OR ai_category IS NOT NULL
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return rows
