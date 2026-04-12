import os
from flask import Flask, render_template
from database import get_all_emails, get_category_counts, get_top_senders, create_table

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

# Create the table automatically when the app starts
# Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS
create_table()


@app.route("/")
def dashboard():
    """Main dashboard page."""
    category_counts = get_category_counts()
    top_senders = get_top_senders(limit=10)
    recent_emails = get_all_emails()[:20]

    chart_labels = [row[0] for row in category_counts]
    chart_values = [row[1] for row in category_counts]

    return render_template(
        "index.html",
        category_counts=category_counts,
        top_senders=top_senders,
        recent_emails=recent_emails,
        chart_labels=chart_labels,
        chart_values=chart_values,
        total_emails=len(get_all_emails())
    )


if __name__ == "__main__":
    print("Starting Email Dashboard...")
    print("Open your browser and go to: http://localhost:5001")
    app.run(host="0.0.0.0", port=5000, debug=True)
