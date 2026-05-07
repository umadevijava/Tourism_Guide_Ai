from backend.core.config import settings
import sqlite3

# Connect to the registry database
db_path = settings.DATABASE_URL.replace('sqlite:///', '')
print('Database path:', db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if documents table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
table_exists = cursor.fetchone() is not None
print('Documents table exists:', table_exists)

if table_exists:
    # Count documents
    cursor.execute('SELECT COUNT(*) FROM documents')
    count = cursor.fetchone()[0]
    print('Documents in database:', count)
    
    # List documents
    if count > 0:
        cursor.execute('SELECT document_id, filename FROM documents')
        for row in cursor.fetchall():
            print('  -', row[0][:10] + '...', row[1])

conn.close()
