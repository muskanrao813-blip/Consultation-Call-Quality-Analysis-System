#!/usr/bin/env python
"""Check what errors the calls have."""
import sqlite3

conn = sqlite3.connect("test.db")
cursor = conn.cursor()

print("=" * 70)
print("CALL ERROR DETAILS")
print("=" * 70)

cursor.execute("SELECT id, appointment_id, status, error_message FROM calls ORDER BY created_at DESC LIMIT 10")
rows = cursor.fetchall()

for call_id, appt_id, status, error in rows:
    print(f"\nCall: {appt_id}")
    print(f"  Status: {status}")
    if error:
        print(f"  Error: {error}")
    else:
        print(f"  Error: None")

conn.close()
