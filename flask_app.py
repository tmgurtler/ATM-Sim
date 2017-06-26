# Python code to handle the server of the ATM logging webapp

from flask import Flask, render_template, url_for, request, redirect, Response
from random import shuffle
import sqlite3
import shortuuid
from flask_sslify import SSLify
from functools import wraps

app = Flask(__name__)
sslify = SSLify(app)

BREAK_AT_X_PINS = 10
NUM_PINS_IN_SUBSET = 5
NUM_TIMES_REPEAT_SUBSET = 3

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'correcthorsebatterystaple' and password == 'password'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/save', methods=["POST"])
def save():
    """This function allows us to record keystroke data by sending a POST to the correct address,
    automatically tabulating it in our database.
    """
    userString = request.form["userString"]
    pinAttempted = request.form["pinAttempted"]
    keyPressed = request.form["keyPressed"]
    time = request.form["time"]
    
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()

    c.execute('INSERT INTO attempts (userString, pinAttempted, keyPressed, time) VALUES (?, ?, ?, ?)', (userString, pinAttempted, keyPressed, time))
    conn.commit()
    conn.close()
    
    # This page isn't meant to be accessed by humans, only the robots automatically POSTing data
    return "You shouldn't be here. :("

@app.route('/reset_db')
@requires_auth
def setup():
    """This function allows us to (wipe and) create our database tables.
    """
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()

    c.execute('DROP TABLE IF EXISTS userStrings')
    c.execute('CREATE TABLE userStrings (userID integer PRIMARY KEY, userString text NOT NULL UNIQUE)')

    c.execute('DROP TABLE IF EXISTS subjects')
    c.execute('CREATE TABLE subjects (userString text PRIMARY KEY, groupLabel text NOT NULL, attempts integer NOT NULL)')

    c.execute('DROP TABLE IF EXISTS attempts')
    c.execute('CREATE TABLE attempts (id integer PRIMARY KEY, userString text NOT NULL, pinAttempted text NOT NULL, keyPressed text NOT NULL, time text NOT NULL)')

    conn.commit()

    conn.close()
    return "Database reset."

@app.route('/reset_attempts')
@requires_auth
def reset_attempts():
    """This function allows us to nuke ONLY the keystroke data (useful to remove prototyping data).
    """
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()

    c.execute('DROP TABLE IF EXISTS attempts')
    c.execute('CREATE TABLE attempts (id integer PRIMARY KEY, userString text NOT NULL, pinAttempted text NOT NULL, keyPressed text NOT NULL, time text NOT NULL)')

    conn.commit()

    conn.close()
    return "Attempts reset."

@app.route('/reset_user/<userID>')
@requires_auth
def reset_user(userID):
    """This function allows us to reset a user's number of attempts back to 0
    (so they go back to the first pinset of their group)
    """
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()

    c.execute('SELECT userString FROM userStrings WHERE userID=?', (userID,))
    res = c.fetchone()
    if res:
        c.execute('UPDATE subjects SET attempts=0 WHERE userString=?', res)
        conn.commit()
        conn.close()
        return "User reset."
    else:
        conn.close()
        return "User did not exist."

@app.route('/make_user', methods=['GET', 'POST'])
@requires_auth
def make_user():
    """This function allows us to make a user and specify what group they're in
    (while setting up the behind the scenes database stuff)
    """
    # on a POST, actually poll the database and create things
    if request.method == 'POST':
        userID = request.form['userID']
        groupLabel = request.form['groupLabel']

        conn = sqlite3.connect('attempts.db')
        c = conn.cursor()
        
        c.execute('SELECT userString FROM userStrings where userID=?', (userID,))
        res = c.fetchone()
        
        # either we've already concocted a string ID for use as a URL, or we'll come up with one now
        if res:
            userString = res[0]
        else:
            userString = shortuuid.uuid()[:5]
            c.execute('INSERT INTO userStrings (userID, userString) VALUES (?,?)', (userID, userString))
        
        c.execute('INSERT INTO subjects (userString, groupLabel, attempts) VALUES (?, ?, ?)', (userString, groupLabel, 0))
        conn.commit()
        
        conn.close()
        return redirect(url_for('get_uid'))
    # otherwise (on a GET), just display an input portal
    else:
        return render_template('user_creation.html')

@app.route('/end/<userString>')
def end(userString):
    """This function arrives at the end of a session and updates the database to reflect
    that a user has undergone a new session.
    """
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()

    c.execute('SELECT * FROM subjects WHERE userString=?', (userString,))
    (userString, group, attempts) = c.fetchone()

    attempts += 1

    c.execute('UPDATE subjects SET attempts=? WHERE userString=?', (attempts, userString))
    conn.commit()
    conn.close()    

    return render_template('end.html')

@app.route('/', methods=['GET', 'POST'])
@app.route('/get_uid', methods=['GET', 'POST'])
def get_uid():
    """This function is the main page for the user side of the experiment.
    We enter a numeric ID, and it automatically forwards us into the experiment pages.
    """
    if request.method == 'POST':
        userID = request.form['userID']
        conn = sqlite3.connect('attempts.db')
        c = conn.cursor()
        
        c.execute('SELECT userString FROM userStrings where userID=?', (userID,))
        res = c.fetchone()
        
        if res:
            userString = res[0]
        else:
            # The user ID does not exist in our DB; return error
            return render_template('uid.html', err=True)
        
        conn.close()
        return redirect(url_for('verify', userString=userString))
    else:
        return render_template('uid.html', err=False)

@app.route('/download')
@requires_auth
def download():
    """This function allows us to pull all the keystroke data from the database and create a human-legible table from it.
    """
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    
    c.execute('SELECT userString, pinAttempted, keyPressed, time FROM attempts')
    res = c.fetchall()
    conn.close()
    
    return render_template('table.html', res=res)

@app.route('/verify/<userString>')
def verify(userString):
    """This function confirms that User ID is valid and sets up variables for the experiment pages
    """
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM subjects where userString=?', (userString,))
    res = c.fetchone()

    if res:
        (userString, group, attempts) = res
        
        # the users will rotate through the sets with different starting points per group
        if group == "A":
            setNumber = attempts
        elif group == "B":
            setNumber = (attempts + 1) % 3
        else:
            setNumber = (attempts + 2) % 3

        ##
        # this will randomize the order of the PINs displayed;
        # each PIN corresponds to a letter ('a', 'b', etc.)
        # and this creates a string of the letters 'a' through 'o' in random order
        orderString = [chr(x) for x in range(ord('a'), ord('a') + 15)]
        shuffle(orderString)
        orderString = ''.join(orderString)
        
        conn.close()
        return render_template('welcome.html', whereTo="practice", userString=userString, setNumber=setNumber, orderString=orderString, holdString="", numThruSet=0, numPinsToBreak=0)
    else:
        # if we got here, something is wrong in the DB; just kick back out to the main page for now
        conn.close()
        return redirect(url_for('get_uid'))

@app.route('/continuer/<userString>', methods=['POST'])
def continuer(userString):
    """This page merely creates a display prompting the user to press enter to continue with the experiment.
    """
    setNumber = int(request.form['setNumber'])
    orderString = request.form['orderString']
    holdString = request.form['holdString']
    numThruSet = int(request.form['numThruSet'])
    numPinsToBreak = int(request.form['numPinsToBreak'])

    return render_template('welcome.html', whereTo="experiment", userString=userString, setNumber=setNumber, orderString=orderString, holdString=holdString, numThruSet=numThruSet, numPinsToBreak=numPinsToBreak)

@app.route('/practice/<userString>', methods=['POST'])
def practice(userString):
    """This page merely creates an area for users to practice with the setup before moving on to the experiment.
    """
    setNumber = int(request.form['setNumber'])
    orderString = request.form['orderString']
    holdString = request.form['holdString']
    numThruSet = int(request.form['numThruSet'])
    numPinsToBreak = int(request.form['numPinsToBreak'])

    return render_template('practice.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString=holdString, numThruSet=numThruSet, numPinsToBreak=numPinsToBreak)

@app.route('/experiment/<userString>', methods=['POST'])
def experiment(userString):
    """This function does most of the heavy lifting routing users through the experiment itself.
    The "pinEntry.html" site helps, where necessary, to change around variables as needed
    (specifically modifying orderString, holdString, and numPinsToBreak),
    but otherwise this function does so for us.
    """
    setNumber = int(request.form['setNumber'])
    orderString = request.form['orderString']
    holdString = request.form['holdString']
    numThruSet = int(request.form['numThruSet'])
    numPinsToBreak = int(request.form['numPinsToBreak'])
    
    # there are no pins left, so go to the end
    if len(orderString) == 0:
        return redirect(url_for('end', userString=userString))

    # every (currently, ten) PINs we give the user a break
    if numPinsToBreak == BREAK_AT_X_PINS:
        return render_template('breakDisplay.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString=holdString, numThruSet=numThruSet, numPinsToBreak=0)
    else:
        # every (currently, five) PINs we repeat what PINs we give the user, and we show them each set of these PINs (currently, three) times
        if len(holdString) == NUM_PINS_IN_SUBSET:
            if numThruSet == (NUM_TIMES_REPEAT_SUBSET - 1):
                # so, after these (three) times, we throw away the repeats and move on
                return render_template('pinEntry.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString="", numThruSet=0, numPinsToBreak=numPinsToBreak)
            else:
                # but in this case, we need to do a repeat, so we put them back in the order string
                return render_template('pinEntry.html', userString=userString, setNumber=setNumber, orderString=(holdString + orderString), holdString="", numThruSet=(numThruSet + 1), numPinsToBreak=numPinsToBreak)
        else:
            # under no special circumstances, just move variables along directly
            return render_template('pinEntry.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString=holdString, numThruSet=numThruSet, numPinsToBreak=numPinsToBreak)
        

    