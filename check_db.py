#!/usr/bin/env python
"""Check database contents."""
import sqlite3

conn = sqlite3.connect("test.db")
cursor = conn.cursor()

print("=" * 60)
print("DATABASE CHECK")
print("=" * 60)

# Count records
print("\nRecord counts:")
for table in ['dieticians', 'calls', 'upload_batches', 'transcripts', 'call_metrics', 'rubric_scores', 'qa_flags', 'feedback_notes']:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count}")

# Show recent calls
print("\nRecent calls:")
cursor.execute("""
    SELECT id, dietician_id, appointment_id, status, error_message
    FROM calls
    ORDER BY created_at DESC
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  {row[2]}: status={row[3]} {('ERROR: ' + row[4]) if row[4] else ''}")

# Show dieticians
print("\nDieticians in system:")
cursor.execute("SELECT id, name, external_id FROM dieticians")
for row in cursor.fetchall():
    print(f"  - {row[1]} (ID: {row[0][:8]}...)")

conn.close()
print("\n" + "=" * 60)
