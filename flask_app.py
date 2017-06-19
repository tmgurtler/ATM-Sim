# Python code to handle the server of the ATM logging webapp

from flask import Flask, render_template, url_for, request, redirect, Response
import sqlite3
import shortuuid
from flask_sslify import SSLify
from functools import wraps

app = Flask(__name__)
sslify = SSLify(app)
pythonanywhere_username = 'tgurtler'

# REWRITE AS A ~POST~ WITH SPECIFIC FIELDS
@app.route('/save/<attempt>')
def save(attempt):
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    c.execute('INSERT INTO attempts VALUES (?)', (attempt,))
    conn.commit()
    conn.close()
    return attempt

# REWRITE FOR THE ACTUAL DATABASES WE WANT
@app.route('/create_db')
def setup():
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    # c.execute('DROP TABLE IF EXISTS attempts')
    c.execute('CREATE TABLE attempts (attempt)')
    # c.execute('DROP TABLE IF EXISTS passwords')
    # c.execute('CREATE TABLE passwords (password)')
    # c.execute('DROP TABLE IF EXISTS uids')
    c.execute('CREATE TABLE uids (uid, email)') # uid, email, password
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

@app.route('/end')
def end():
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
    result = ''
    vars = ''
    if request.method == 'POST':
        email = request.form['userID']
        conn = sqlite3.connect('attempts.db')
        c = conn.cursor()
        c.execute('SELECT uid FROM uids where email=?', (email,))
        res = c.fetchone()
        if res:
            vars = res[0]
        else:
            uid = shortuuid.uuid()[:5]
            c.execute('INSERT INTO uids VALUES (?,?)', (uid, email))
            conn.commit()
            vars = uid
        conn.close()
        return redirect(url_for('experiment', uid=vars))
    return render_template('uid.html', result=result)

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

# Confirms that User ID is valid, and renders the experiment for them.
# Shouldn't change unless we change that underlying DB
@app.route('/experiment/<uid>')
def experiment(uid):
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    c.execute('SELECT uid FROM uids where uid=?', (uid,))
    res = c.fetchone()
    if res:
        return render_template('experiment.html', uid=uid)
    else:
        return redirect(url_for('get_uid'))
