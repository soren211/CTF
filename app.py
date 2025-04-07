from flask import Flask, render_template, request, redirect, session, make_response
from flask.sessions import SecureCookieSession, SessionInterface
from werkzeug.datastructures import CallbackDict
import sqlite3
from cryptography.fernet import Fernet
import base64
import os

app = Flask(__name__, template_folder='templates')

# Configure server settings
app.config.update(
    SECRET_KEY="supersecretkey", 
    SERVER_NAME='localhost:5001',
    PREFERRED_URL_SCHEME='http'
)



# Encryption setup
raw_key = b"IT101_CTF_Key_32bytes_long_12345"
key = base64.urlsafe_b64encode(raw_key)
cipher = Fernet(key)

# Database initialization
def init_db():
    try:
        if os.path.exists('database.db'):
            os.remove('database.db')
            
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                is_admin BOOLEAN
            )
        """)
        
        cursor.execute("""
            CREATE TABLE secrets (
                id INTEGER PRIMARY KEY,
                flag TEXT
            )
        """)
        
        cursor.execute("INSERT INTO users VALUES (1, 'admin', 'password123', 1)")
        cursor.execute("INSERT INTO users VALUES (2, 'user', 'password123', 0)")
        
        flag = "IT101{YOU_G0T_M3_S053N}"
        cursor.execute("INSERT INTO secrets VALUES (1, ?)", (flag,))
        
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

# Nuclear reset endpoint
@app.route('/nuke_everything')
def nuke_everything():
    """Complete system reset"""
    session.clear()
    if os.path.exists('database.db'):
        os.remove('database.db')
    init_db()
    resp = make_response(redirect('/'))
    resp.set_cookie('session', '', expires=0)
    resp.delete_cookie('role')
    return resp

# Main routes
@app.route("/")
def home():
    if "username" in session:
        if session.get("is_admin"):
            return render_template("admin.html")
        return render_template("user.html")
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session["username"] = user[1]
        session["is_admin"] = bool(user[3])
        return redirect("/")
    return "Login failed! <a href='/'>Try again</a>"


# Admin functionality
@app.route("/admin/search", methods=["GET", "POST"])
def admin_search():
    if request.method == "POST":
        query = request.form.get("query", "")
        print(f"Query: {query}")

        # Vulnerable SQL query - directly using the input (SQL injection)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            cursor.execute(f"SELECT flag FROM secrets WHERE id={query}")
            result = cursor.fetchone()  # Fetch the result of the query
            if result:
                # Return the flag if found
                return f"Result: {result[0]}"
            return "No results found"
        except Exception as e:
            # Return any errors (optional)
            return f"An error occurred: {e}"
        finally:
            conn.close()

    return "Method Not Allowed"


# Debug endpoint
@app.route('/debug')
def debug():
    return {
        'session': dict(session),
        'cookies': request.cookies,
        'is_admin': session.get('is_admin', False)
    }

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)