from flask import Flask, redirect, request, jsonify
import sqlite3
import secrets

app = Flask(__name__)
DB = "urls.db"

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS urls (id TEXT PRIMARY KEY, long_url TEXT, hits INT)")
    conn.commit()
    conn.close()

# Endpoint 1: Shorten URL
@app.route("/shorten", methods=["POST"])
def shorten():
    long_url = request.json.get("url")
    short_id = secrets.token_urlsafe(4)  # e.g., "abc123"
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO urls (id, long_url, hits) VALUES (?, ?, 0)", (short_id, long_url))
    conn.commit()
    conn.close()
    return jsonify({"short_url": f"https://youtube.com/{short_id}"})

# Endpoint 2: Redirect (YOUR NEW CODE GOES HERE)
@app.route("/<short_id>")
def redirect_to_long(short_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE urls SET hits = hits + 1 WHERE id = ?", (short_id,))
    cursor.execute("SELECT long_url FROM urls WHERE id = ?", (short_id,))
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return "URL not found", 404
    return redirect(result[0], code=302)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)