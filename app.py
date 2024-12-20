import os #module, which provides a way to interact with the operating system

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session #a tool for session administering on the server side
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required

app = Flask(__name__) #initiates Flask application, gives name to app

app.config['APPLICATION_ROOT'] = '/osurgen'
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

OPTIONS = []

@app.route("/")
#decorator calls function which wraps the original defined below with additional logic
@login_required
def index():

    username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]


    # A.I helped with aliasing the AQL query
    surveys = db.execute("SELECT surveys.id AS survey_id, surveys.question, surveys.time, users.username FROM surveys JOIN users ON users.id = surveys.creator WHERE status = 'active' ORDER BY survey_id DESC LIMIT 5")
    user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
    #Needed to display correct form for each survey
    vote_check = []
    surveys_voted = db.execute("SELECT * FROM voted WHERE user = ?", session['user_id'])
    for survey in surveys_voted:
        vote_check.append(survey['survey'])

    return render_template("index.html", username=username, surveys=surveys, user=user, vote_check=vote_check)

@app.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    
    if request.method == "GET":
        return render_template("generate.html")
    
    else:
        question = request.form.get("question")
        options = request.form.getlist("option")
        time = datetime.now()

        if len(options) < 2:
            warning = "Please add at least two options for the survey"
            return render_template("generate.html", warning=warning)
        if not question:
            warning = "Please provide a question for your survey"
            return render_template("generate.html", warning=warning)
        
        db.execute("INSERT INTO surveys (creator, question, time) VALUES (?, ?, ?)",
                       session["user_id"], question, time)
        
        survey = db.execute("SELECT id FROM surveys WHERE time = ?", time)[0]['id']
        
        for option in options:
            db.execute("INSERT INTO options (survey, option) VALUES (?, ?)",
                       survey, option)


        return redirect(url_for('surveys'))

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
        session["username"] = user_check[0]["username"]

        return redirect(url_for('index'))        

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for('index'))

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
        
@app.route("/results", methods=["GET", "POST"])
@login_required
def results():

    if request.method == "POST":

        global OPTIONS
        chosen = request.form.get("chosen")
        survey = request.form.get("survey")
        check_vote = db.execute("SELECT * FROM voted WHERE user = ? AND survey = ?", session["user_id"], survey)
        question = db.execute("SELECT question FROM surveys WHERE id = ?", survey)[0]['question']
        labels_dict = db.execute("SELECT option FROM options WHERE survey = ?", survey)
        labels = []
        for label in labels_dict:
            labels.append(label['option'])
        votes = []
        votes_dict = db.execute("SELECT points FROM options WHERE survey= ?", survey)
        for vote in votes_dict:
            votes.append(vote['points'])

        #Verifies if the option which was sent is available for this survey
        if chosen not in OPTIONS:
            warning = "Failure. Option not available for this survey."
            return render_template("failure.html", warning=warning)
        #Checks wether the user has voted in this survey
        elif len(check_vote) > 0:
            warning = "Failure. You have already voted in this survey."
            return render_template("failure.html", warning=warning)
            
        #Registers the vote and that the user voted in this survey
        else:
            db.execute("INSERT INTO voted (user, survey) VALUES(?, ?)", session["user_id"], survey)
            db.execute("UPDATE options SET points = points + 1 WHERE survey = ? AND option = ?", survey, chosen)
            votes = []
            votes_dict = db.execute("SELECT points FROM options WHERE survey= ?", survey)
            for vote in votes_dict:
                votes.append(vote['points'])

            return render_template('results.html', question=question, labels=labels, votes=votes)
    else:
        return render_template('results.html', question=question, labels=labels, votes=votes)

@app.route("/surveys", methods=["GET", "POST"])
@login_required
def surveys():

    if request.method == "GET":
        # A.I helped with aliasing the AQL query
        surveys = db.execute("SELECT surveys.id AS survey_id, surveys.question, surveys.time, users.username FROM surveys JOIN users ON users.id = surveys.creator WHERE status = 'active'")
        user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
        #Needed to display correct form for each survey
        vote_check = []
        surveys_voted = db.execute("SELECT * FROM voted WHERE user = ?", session['user_id'])
        for survey in surveys_voted:
            vote_check.append(survey['survey'])

        return render_template("surveys.html", surveys=surveys, user=user, vote_check=vote_check)

#Below is the form handling 'cross-road' with branches for different input        
@app.route("/handle_form", methods=["GET", "POST"])
@login_required
def handle_form():
        
    action = request.form['action']
    survey_id = request.form.get('id')

    if action == 'delete':
        return redirect(url_for('delete', survey_id=survey_id))
    elif action == 'vote':
        return redirect(url_for('vote', survey_id=survey_id))
    elif action == 'results':
        return redirect(url_for('result', survey_id=survey_id))

#the variable is passed in the rout...
@app.route("/delete/<int:survey_id>", methods=["GET", "POST"])
@login_required
#... and then passed into the function as a parameter
def delete(survey_id):
    db.execute("UPDATE surveys SET status = 'deleted' WHERE id =?", survey_id)
    #db.execute("DELETE FROM options WHERE survey = ?", survey_id)
    #db.execute("DELETE FROM voted WHERE survey = ?", survey_id)
    #db.execute("DELETE FROM surveys WHERE id = ?", survey_id)
    return redirect(url_for("surveys"))

@app.route("/vote/<int:survey_id>", methods=["GET", "POST"])
@login_required
def vote(survey_id):
    question = db.execute("SELECT question FROM surveys WHERE id = ?", survey_id)[0]["question"]
    options = db.execute("SELECT * FROM options WHERE survey = ?", survey_id)
    
    global OPTIONS
    OPTIONS = []
    for option in options:
        OPTIONS.append(option['option'])

    return render_template('vote.html', survey_id=survey_id, question=question, vote_options=OPTIONS)

@app.route("/result/<int:survey_id>", methods=["GET", "POST"])
@login_required
def result(survey_id):

    question = db.execute("SELECT question FROM surveys WHERE id = ?", survey_id)[0]["question"]
    
    labels = []
    labels_dict = db.execute("SELECT option FROM options WHERE survey = ?", survey_id)
    for label in labels_dict:
        labels.append(label['option'])
    
    votes = []
    votes_dict = db.execute("SELECT points FROM options WHERE survey= ?", survey_id)
    for vote in votes_dict:
        votes.append(vote['points'])

    return render_template('result.html', question=question, labels=labels, votes=votes)

@app.route("/search")
@login_required
def search():
    return render_template("search.html")


@app.route("/search_responseq")
@login_required
def search_responseq():

    q = request.args.get("q")

    if q:
        surveys = db.execute("SELECT surveys.id AS survey_id, surveys.question, surveys.time, users.username FROM surveys JOIN users ON users.id = surveys.creator WHERE question LIKE ? AND status = 'active'", "%" + q + "%")
    else:
        surveys = []

    user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
    
    #Needed to display correct form for each survey
    vote_check = []
    surveys_voted = db.execute("SELECT * FROM voted WHERE user = ?", session['user_id'])
    for survey in surveys_voted:
        vote_check.append(survey['survey'])

    #data sent as resposne to dynamic search on the user's side.
    return jsonify(surveys=surveys, user=user, vote_check=vote_check)

@app.route("/search_responsec")
@login_required
def search_responsec():

    c = request.args.get("c")

    if c:
        surveys = db.execute("SELECT surveys.id AS survey_id, surveys.question, surveys.time, users.username FROM surveys JOIN users ON users.id = surveys.creator WHERE users.username LIKE ? AND status = 'active'", "%" + c + "%")
    else:
        surveys = []

    user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
    
    #Needed to display correct form for each survey
    vote_check = []
    surveys_voted = db.execute("SELECT * FROM voted WHERE user = ?", session['user_id'])
    for survey in surveys_voted:
        vote_check.append(survey['survey'])

    #data sent as resposne to dynamic search on the user's side.
    return jsonify(surveys=surveys, user=user, vote_check=vote_check)

@app.route("/search_date", methods = ["GET", "POST"])
@login_required
def search_date():

    
    if request.method == "POST":
        start = request.form.get("date_start")
        end = request.form.get("date_end")
        
        start += " 00.00.00" #This needs to be added at the end of the date string to match data in time column in surveys table
        end += " 23:59:59"

        surveys = db.execute("SELECT surveys.id AS survey_id, surveys.question, surveys.time, users.username FROM surveys JOIN users ON users.id = surveys.creator WHERE time BETWEEN ? AND ? AND status = 'active'", start, end)

        user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
        
        vote_check = []
        surveys_voted = db.execute("SELECT * FROM voted WHERE user = ?", session['user_id'])
        for survey in surveys_voted:
            vote_check.append(survey['survey'])

        return render_template("search.html", surveys=surveys, user=user, vote_check=vote_check)

@app.route("/archive")
@login_required
def archive():

    surveys = db.execute("SELECT surveys.id AS survey_id, surveys.question, surveys.time, users.username FROM surveys JOIN users ON users.id = surveys.creator WHERE status = 'deleted'")

    return render_template("archive.html", surveys=surveys)

@app.route("/account", methods = ["GET", "POST"])
@login_required
def account():

    if request.method == "GET":
        return render_template("account.html")
    else:
        old_password = db.execute("SELECT hash FROM users WHERE id = ?",
                                  session["user_id"])[0]["hash"]
        
        if not check_password_hash(old_password, request.form.get("oldPassword")):
            warning = "Invalid password"
            return render_template("account.html", warning=warning)
        if not request.form.get("oldPassword"):
            warning = "Provide your old password"
            return render_template("account.html", warning=warning)
        if not request.form.get("newPassword"):
            warning = "Must provide valid new password"
            return render_template("account.html", warning=warning)
        if request.form.get("oldPassword") == request.form.get("newPassword"):
            warning = "New passwrod must be different than old password"
            return render_template("account.html", warning=warning)
        if request.form.get("newPassword") != request.form.get("confirmation"):
            warning = "Repeated password must be the same as new password"
            return render_template("account.html", warning=warning)
        
        new_password = generate_password_hash(request.form.get("newPassword"))
        db.execute("UPDATE users SET hash = ? WHERE id =?", new_password, session["user_id"])

        session.clear()
        return render_template("login.html")

@app.route("/about")
def about():
    return render_template("about.html")
