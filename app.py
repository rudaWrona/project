import os #module, which provides a way to interact with the operating system

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session #a tool for session administering on the server side
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required

app = Flask(__name__) #initiates Flask application, gives name to app

app.config["SESSION_PERMANENT"] = False #session will  be concludet when conncetion terminates.
app.config["SESSION_TYPE"] = "filesystem"
Session(app) #commences session so that session files could be administerd on the server side

db = SQL("sqlite:///FP_database.db")

#makes sure the responses are not cashed and always fresh data is sent to the user
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
#decorator calls function which wraps the original defined below with additional logic
@login_required
def index():

    username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

    return render_template("index.html", username=username)

@app.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    
    if request.method == "GET":
        return render_template("generate.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    
    session.clear()

    if request.method == "GET":
        return render_template("login.html")
    
    else:
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            warning = "Please enter a username"
            return render_template("login.html", warning=warning)
        elif not password:
            warning = "Please enter a password"
            return render_template("login.html", warning=warning)
        
        user_check = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(user_check) != 1 or not check_password_hash(user_check[0]["hash"], password):
            warning = "invalid username and/or password"
            return render_template("login.html", warning=warning)

        session["user_id"] = user_check[0]["id"]

        return redirect("/")        

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    
    if request.method == "GET":
        return render_template("register.html")
    
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        #validate the registration input
        if not username:
            warning = "Please enter a username"
            return render_template("register.html", warning=warning)
        elif not password:
            warning = "Please enter a password"
            return render_template("register.html", warning=warning)
        elif password != confirmation:
            warning = "Password and confirmation must match"
            return render_template("register.html", warning=warning)
        
        #using werkzeug.security hash the password
        hashed_password = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                       username, hashed_password)
            return render_template("login.html")
        # cs50.SQL.execute will treat a duplicate username as an ValueError due to UNIQUE INDEX on username column
        except ValueError:
            warning = "Username taken"
            return render_template("register.html", warning=warning)
        
#this should make the aplication update automaticly when working after changes but does not.
if __name__ == "__main__":
    app.run(debug=True)