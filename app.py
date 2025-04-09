from flask import Flask, render_template, request, redirect, session, make_response
from flask.sessions import SecureCookieSession, SessionInterface
from werkzeug.datastructures import CallbackDict
import sqlite3
from cryptography.fernet import Fernet
import base64
import os

app = Flask(__name__, template_folder='templates')

app.config.update(
    SECRET_KEY="supersecretkey"
)

'''
 less obvious but more clear instrucution
 cookie for admin be a truefalse 1 or 0 
 better website 
 SQLlite is bad go to normal 
 cool cool
 



'''

raw_key = b"IT101_CTF_Key_32bytes_long_12345"
key = base64.urlsafe_b64encode(raw_key)
cipher = Fernet(key)



# Database 
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
        
        raw_flag = "IT101{S053N5_F1AG_19384372}"

        
        data_bytes = raw_flag.encode('utf-8')
        encoded_bytes = base64.b64encode(data_bytes)
        flag = encoded_bytes.decode('utf-8')

        cursor.execute("INSERT INTO secrets VALUES (239294, ?)", (flag,))
        
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()


@app.route("/")
def home():
    return "CTF is working! Routes: /login, /admin/search, /debug"

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
        # Check the cookie (convert string to int)
        is_admin = int(request.cookies.get("is_admin", 0))
        if is_admin:
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
        # Set  cookie (1 for admin, 0 for regular user)
        is_admin = 1 if user[3] else 0
        resp = make_response(redirect("/"))
        resp.set_cookie("is_admin", str(is_admin))  #  1/0 value
        return resp
    return "Login failed! <a href='/'>Try again</a>"

@app.route("/admin/search", methods=["POST"])
def admin_search():
    is_admin = int(request.cookies.get("is_admin", 0))
    if not is_admin:
        return "Access denied!", 403
        
    query = request.form.get("query", "").strip()
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
      
        cursor.execute(f"SELECT flag FROM secrets WHERE id={query}")
        result = cursor.fetchone()
        if result:
            flag = result[0]
            message = f"Flag found: {flag}\n\nThis appears to be encoded. Try decoding it from base64!"
            return render_template("admin.html", 
                                result=message,
                                error=False)
        return render_template("admin.html", 
                            result='No results found',
                            error=False)
    except sqlite3.Error as e:
       
        return render_template("admin.html", 
                            result=f"Database error: {str(e)}",
                            error=True)
    except Exception as e:
  
        return render_template("admin.html",
                            result=f"Error: {str(e)}",
                            error=True)
    finally:
        if 'conn' in locals():
            conn.close()


@app.route('/debug')
def debug():
    return {
        'session': dict(session),
        'cookies': request.cookies,
        'is_admin_cookie': request.cookies.get("is_admin", "Not set")
    }

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)