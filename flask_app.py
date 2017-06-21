# Python code to handle the server of the ATM logging webapp

from flask import Flask, render_template, url_for, request, redirect, Response
from random import shuffle
import sqlite3
import shortuuid
from flask_sslify import SSLify
from functools import wraps

app = Flask(__name__)
sslify = SSLify(app)

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'palevipr' and password == 'palevipr'

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

# REWRITE AS A ~POST~ WITH SPECIFIC FIELDS
@app.route('/save', methods=["POST"])
def save():
    userString = request.form["userString"]
    pinAttempted = request.form["pinAttempted"]
    keyPressed = request.form["keyPressed"]
    time = request.form["time"]
    
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()

    c.execute('INSERT INTO attempts (userString, pinAttempted, keyPressed, time) VALUES (?, ?, ?, ?)', (userString, pinAttempted, keyPressed, time))
    conn.commit()
    conn.close()
    
    return "You shouldn't be here. :("

# REWRITE FOR THE ACTUAL DATABASES WE WANT
@app.route('/create_db')
@requires_auth
def setup():
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
    return "OK"

##
# ONLY REACTIVATE IF WE WANT TO BE ABLE TO NUKE DATABASE AT WILL (BAD IDEA)
#
# @app.route('/reset_attempts')
# def reset():
#     conn = sqlite3.connect('attempts.db')
#     c = conn.cursor()
#     c.execute('DROP TABLE IF EXISTS attempts')
#     c.execute('CREATE TABLE attempts (attempt)')
#     conn.commit()
#     conn.close()
#     return "OK"

@app.route('/end/<userString>')
def end(userString):
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()

    c.execute('SELECT * FROM subjects WHERE userString=?', (userString,))
    (userString, group, attempts) = c.fetchone()

    attempts += 1

    c.execute('UPDATE subjects SET attempts=? WHERE userString=?', (attempts, userString))
    conn.commit()
    conn.close()    

    return render_template('end.html')

##
# With a GET request, this will display the prompt to enter a User ID. When entered, it will POST to itself to generate the link to go to
#
# With a POST request, this will find the internal representation of the ID, and generate a link for a unique experiment from it
#
# (I don't think this needs edited much, although the underlying DB might change)
@app.route('/', methods=['GET', 'POST'])
@app.route('/get_uid', methods=['GET', 'POST'])
def get_uid():
    if request.method == 'POST':
        userID = request.form['userID']
        conn = sqlite3.connect('attempts.db')
        c = conn.cursor()
        
        c.execute('SELECT userString FROM userStrings where userID=?', (userID,))
        res = c.fetchone()
        
        if res:
            userString = res[0]
        else:
            userString = shortuuid.uuid()[:5]
            c.execute('INSERT INTO userStrings (userID, userString) VALUES (?,?)', (userID, userString))
            conn.commit()
        
        conn.close()
        return redirect(url_for('verify', userString=userString))
    else:
        return render_template('uid.html')

# Note that currently, "attempts" is just a huge list of JSON strings. Can we improve this?
@app.route('/download')
@requires_auth
def download():
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM attempts')
    res = c.fetchall()
    conn.close()
    return str(res)

# Confirms that User ID is valid and sets up experiment variables
@app.route('/verify/<userString>')
def verify(userString):
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM subjects where userString=?', (userString,))
    res = c.fetchone()

    if res:
        (userString, group, attempts) = res
        
        if group == "A":
            setNumber = attempts
        elif group == "B":
            setNumber = (attempts + 1) % 3
        else:
            setNumber = (attempts + 2) % 3

        orderString = [chr(x) for x in range(ord('a'), ord('a') + 15)]
        shuffle(orderString)
        orderString = ''.join(orderString)
        
        conn.close()
        return render_template('redirect.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString="", numThruSet=0, numThruPin=(-1))
    else:
        conn.close()
        return redirect(url_for('get_uid'))

# Renders experiment pages
# note: although most rerouting happens here, this does expect that numThruPin gets set properly on pinEntry.html
@app.route('/experiment/<userString>', methods=['POST'])
def experiment(userString):
    setNumber = int(request.form['setNumber'])
    orderString = request.form['orderString']
    holdString = request.form['holdString']
    numThruSet = int(request.form['numThruSet'])
    numThruPin = int(request.form['numThruPin'])
    
    if numThruPin == -1:
        return render_template('pinDisplay.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString=holdString, numThruSet=numThruSet, numThruPin=0)
    elif numThruPin == 3:
        holdString += orderString[0]
        orderString = orderString[1:]
        if len(holdString) == 5:
            if numThruSet == 2:
                if len(orderString) == 0:
                    return redirect(url_for('end', userString=userString))
                else:
                    return render_template('breakDisplay.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString="", numThruSet=0, numThruPin=(-1))
            else:
                return render_template('breakDisplay.html', userString=userString, setNumber=setNumber, orderString=(holdString + orderString), holdString="", numThruSet=(numThruSet + 1), numThruPin=(-1))
        else:
            return render_template('redirect.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString=holdString, numThruSet=numThruSet, numThruPin=(-1))
    else:
        return render_template('pinEntry.html', userString=userString, setNumber=setNumber, orderString=orderString, holdString=holdString, numThruSet=numThruSet, numThruPin=numThruPin)

    