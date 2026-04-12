import os
from dotenv import load_dotenv
import anthropic
from read_emails import authenticate
from database import create_table, save_email

# Load API key — look for .env next to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

CATEGORIES = {
    "urgent":     "🔴 Urgent",
    "work":       "💼 Work",
    "finance":    "💰 Finance",
    "newsletter": "📰 Newsletter",
    "personal":   "👤 Personal",
    "spam":       "🗑️  Spam",
    "other":      "📦 Other",
}


def categorize_email(client, sender, subject, preview):
    """Send email details to Claude and get a category back."""
    prompt = f"""You are an email categorization assistant. Categorize the following email into exactly one of these categories:
- urgent (time-sensitive, requires immediate action)
- work (professional, job-related, not urgent)
- finance (bills, statements, payments, banking)
- newsletter (marketing, subscriptions, digests)
- personal (friends, family, personal matters)
- spam (unwanted, suspicious, junk)
- other (anything that doesn't fit above)

Email details:
From: {sender}
Subject: {subject}
Preview: {preview}

Reply with just the category word in lowercase. Nothing else."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}]
    )

    category = message.content[0].text.strip().lower()
    return category, CATEGORIES.get(category, CATEGORIES["other"])


def clean_preview(text):
    """Strip invisible email spacer characters from preview text."""
    return ''.join(c for c in text if c.isprintable() and ord(c) < 8000)


def get_and_categorize_emails(max_results=10):
    """Main function — fetch, categorize, and save emails."""

    # Make sure the database and table exist
    create_table()

    print("Connecting to Gmail...\n")
    gmail_service = authenticate()

    print("Connecting to Claude...\n")
    claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    results = gmail_service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        print("No emails found.")
        return

    print(f"Processing {len(messages)} emails...\n")
    print("=" * 60)

    new_count = 0
    skipped_count = 0

    for msg in messages:
        email_data = gmail_service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers = email_data.get("payload", {}).get("headers", [])
        subject = next((h["value"]
                       for h in headers if h["name"] == "Subject"), "No subject")
        sender = next((h["value"]
                      for h in headers if h["name"] == "From"), "Unknown")
        date = next((h["value"]
                    for h in headers if h["name"] == "Date"), "Unknown")
        preview = clean_preview(email_data.get("snippet", ""))
        msg_id = msg["id"]

        # Categorize with Claude
        raw_category, display_category = categorize_email(
            claude_client, sender, subject, preview)

        # Save to database — returns True if new, False if already saved
        was_inserted = save_email(
            msg_id, sender, subject, date, preview, display_category)

        if was_inserted:
            new_count += 1
            status = "✅ Saved"
        else:
            skipped_count += 1
            status = "⏭️  Already saved"

        print(f"Category: {display_category}  {status}")
        print(f"From:     {sender}")
        print(f"Date:     {date}")
        print(f"Subject:  {subject}")
        print(f"Preview:  {preview[:100]}...")
        print("-" * 60)

    print(f"\n✅ {new_count} new emails saved")
    print(f"⏭️  {skipped_count} duplicates skipped")
    print("\nRun 'python database.py' to see a summary of your inbox.")


if __name__ == "__main__":
    get_and_categorize_emails(max_results=10)
