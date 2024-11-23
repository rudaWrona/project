
# ONLINE SURVEY GENERATOR
## Video Demo: <https://youtu.be/Cz7DBUaJQT4>
## Description:
### Foreword
My final project application is called **OSV**, which stands for **Online Survey Generator**.
This application is currently running online on a website that I administer. Here's [the link that leads to that site](https://vanilladice.pl/osurgen/). All the paths and routes in the code are formatted exactly as they are on the server. This means the application will not run in its current form without adjusting the paths. The directory also contains files necessary for running the application on the server (e.g., passenger_wsgi.py). I also set the configuration to match the server's folder structure by adding this line: `app.config['APPLICATION_ROOT'] = '/osurgen'`. This makes the /osurgen directory the root folder for all the app's paths.

The application uses many tools taught and practiced during the CS50 course. It slightly extends the knowledge I gained while watching the lectures and completing problem sets. This is a Flask application that uses SQL queries for database operations and JavaScript for client-side display. I used some solutions discussed in the course, such as the `login_required()` function in the helpers.py file, and the `login()` and `logout()` functions from the app.py file. Additionally, I used `check_password_hash` and `generate_password_hash` from the werkzeug.security module. I also used Flask sessions, configuring them in the app.py file as demonstrated in the course. I used Bootstrap elements from the problem sets in the course. They were sufficient for the needs of my final project. I asked some friends to help me test the program.

### What it does
The application is designed as a tool for creating personalized online surveys, which can then be shared with other users of the application. Users can vote in any available surveys. Once a user has voted, the survey results are shown to them in the form of a bar chart. Each user can vote in a given survey only once. Users also have the option to delete their own surveys and dynamically search for surveys.

### The files
The main file is app.py, which contains most of the Python functions. Many of these are decorated with login_required, meaning that all users must register and log in to access the application's features. For this project, I created a database file using SQLite3 called FP_database.db. All SQL queries are done using the CS50 library. All HTML files are rendered via Flask routes and Python functions related to them.

#### "/"
The user is redirected here after logging in. It’s also accessible by clicking "OSG" at the top of the site. This route renders the index.html file. The front page shows a table of the five most recent surveys added to the database. Every table on the site shows the survey’s title/question, its ID number, its creator, the time of creation, and the available actions. The actions vary depending on whether the user is the creator of the survey or if they have already voted in that particular survey.

#### "/generate"
Accessible via the "Make Survey" button. It renders the generate.html file, which contains a form that allows users to create a new survey. Users must provide a question/title for the survey. The server checks if the title has been submitted. Users must also provide available options—at least two options are required, since users need choices for voting. The submitted data is then saved in two SQL tables called surveys and options. The first table stores data related to the survey, while the second stores information about the available options and the number of votes for each. This design decision was based on what I learned in the course.

#### "/login"
This route works similarly to the one in the Flask problem set. It clears the session and checks whether the data submitted via POST (username and password) is valid. All validation is done server-side. Afterward, the user is redirected to the index page.

#### "/logout"
Clears the session and redirects to the index page.

#### "/register"
Accessed by Register button visible for unlogged users. Renders the register.html file, which contains a form for registering users. Users must provide a username and a password, and the password must be confirmed (entered twice). All data is validated on the server side, and warnings are displayed if something is incorrect. Passwords are hashed using the `generate_password_hash()` function and stored in the users table in the database. The `cs50.SQL.execute` method treats duplicate usernames as a ValueError due to the UNIQUE INDEX on the username column, triggering a warning. If everything is correct, the user is registered and then redirected to the login page.

#### "/results"
Shows the results of a survey via the results.html file. This route can be accessed using either the GET or POST method. If accessed via GET, the page displays a bar chart using the Chart.js library. The appropriate data, such as the survey title, labels (options), and points (votes), is passed as JSON. This is handled by Jinja’s tojson function.

If accessed via POST (from a voting form), the program checks whether the user has already voted in the survey and whether the submitted option is valid. Only then is the new vote registered in the database, and the updated results are shown.

#### "/surveys"
Displays all available surveys via the surveys.html file. The table is similar to the one on the index page but contains all surveys. The action column is rendered differently for each user, depending on whether the user is the survey’s creator. It also contains a form for submitting data.

#### "/handle_form"
This route serves as a “crossroad” for data submitted via forms, like the ones described above. It handles requests for deleting a survey (if the creator wants to delete it), voting (if the user wants to submit a vote), or viewing results (if the user has already voted). The returned value is the survey’s ID (survey_id), which is included in the URL and passed to the next route.

#### "/delete/int:survey_id"
This route changes the status column of the specified survey to "deleted", making it no longer available for voting, but still accessible in the archive section.

#### "/vote/int:survey_id"
This route prepares a voting form. It retrieves the survey title and options and passes them to the vote.html file using Jinja. The options are displayed as radio buttons, which the user can select and submit. After voting, the user is redirected to the results page.

#### "/result/int:survey_id"
This is similar to the /results route but simply shows the current state of the votes for the specified survey.

#### "/search"
This route renders the search.html file, which allows users to search for surveys. Users can search dynamically by survey title/question or the creator’s name. Users can also search by date using a date range.

This HTML file contains the most complex JavaScript code in the application. The two input fields (for title and creator) send queries to the database and receive responses in JSON format (by `"/search_responseq"` and `"/search_responsec"` routs in app.py), which are then used to dynamically render a table of results using JavaScript. I believe there is room for improvement in this search function, but it currently works as intended.

#### "/search_date"
This is the third search option, allowing users to search by the survey's creation time. It’s essentially a simple HTML form that sends data (in the form of a date and time) to the server.

#### "/archive"
This route renders the archive.html file, which shows a table of deleted surveys.

#### "/account"
This route allows users to change their password. The user must confirm the change by providing their current password. All validation is done server-side, and the new password is hashed and stored in the database. After changing their password, the user must re-login. I am thinking about adding new options here later.

#### "/about"
A simple page providing basic information about the application.

### The Database
The following tables were created in the database for this project:

- users: Information about registered users.
- surveys: Information about surveys created in the application.
- options: Available survey options and the number of votes for each.
- voted: Information in which surveys users have already voted.