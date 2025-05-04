from flask import Flask, redirect, request, jsonify
import sqlite3
import secrets
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
DB = "urls.db"
metrics = PrometheusMetrics(app)  # Initialize Prometheus metrics

# Custom metrics
url_created = metrics.counter(
    'url_created_total', 
    'Total number of URLs shortened',
    labels={'endpoint': 'shorten'}
)

url_redirected = metrics.counter(
    'url_redirected_total',
    'Total number of URL redirects',
    labels={'endpoint': 'redirect'}
)

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id TEXT PRIMARY KEY, 
            long_url TEXT, 
            hits INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Endpoint 1: Shorten URL
@app.route("/shorten", methods=["POST"])
@url_created  # Track this endpoint
def shorten():
    long_url = request.json.get("url")
    if not long_url:
        return jsonify({"error": "URL is required"}), 400
        
    short_id = secrets.token_urlsafe(4)
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO urls (id, long_url, hits) VALUES (?, ?, 0)",
            (short_id, long_url)
        )
        conn.commit()
        return jsonify({
            "short_url": f"http://yourdomain.com/{short_id}",
            "original_url": long_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Endpoint 2: Redirect
@app.route("/<short_id>")
@url_redirected  # Track this endpoint
def redirect_to_long(short_id):
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        
        # Record hit and get URL
        cursor.execute("""
            UPDATE urls 
            SET hits = hits + 1 
            WHERE id = ?
            RETURNING long_url
        """, (short_id,))
        
        result = cursor.fetchone()
        conn.commit()
        
        if not result:
            metrics.incr('url_not_found_total')
            return "URL not found", 404
            
        return redirect(result[0], code=302)
    finally:
        conn.close()

# Add default metrics endpoint at /metrics
metrics.register_default(
    metrics.counter(
        'by_path_counter', 
        'Request count by request paths',
        labels={'path': lambda: request.path}
    )
)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)