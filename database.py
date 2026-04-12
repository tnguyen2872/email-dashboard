import sqlite3
import os
from datetime import datetime

# Always store the database file next to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "emails.db")


def get_connection():
    """Get a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)


def create_table():
    """Create the emails table if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id  TEXT UNIQUE,        -- Gmail's unique ID, prevents duplicates
            sender      TEXT,
            subject     TEXT,
            date        TEXT,
            preview     TEXT,
            category    TEXT,
            created_at  TEXT                -- when we saved this record
        )
    """)

    conn.commit()
    conn.close()
    print("Database ready.")


def save_email(message_id, sender, subject, date, preview, category):
    """Save a categorized email to the database.
    
    Uses INSERT OR IGNORE so duplicate emails are silently skipped.
    This means you can run the script multiple times safely.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO emails 
            (message_id, sender, subject, date, preview, category, created_at)
        VALUES 
            (?, ?, ?, ?, ?, ?, ?)
    """, (
        message_id,
        sender,
        subject,
        date,
        preview,
        category,
        datetime.now().isoformat()
    ))

    # cursor.rowcount tells us if the row was inserted or skipped
    was_inserted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return was_inserted


def get_all_emails():
    """Fetch all saved emails, newest first."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT message_id, sender, subject, date, preview, category, created_at
        FROM emails
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_category_counts():
    """Get a count of emails per category — useful for the dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM emails
        GROUP BY category
        ORDER BY count DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_top_senders(limit=10):
    """Get the senders who email you most."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sender, COUNT(*) as count
        FROM emails
        GROUP BY sender
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    # Run this file directly to test the database setup
    create_table()

    # Print a summary of what's in the database
    print("\n--- Category breakdown ---")
    for category, count in get_category_counts():
        print(f"  {category}: {count} emails")

    print("\n--- Top senders ---")
    for sender, count in get_top_senders():
        print(f"  {count}x  {sender}")
