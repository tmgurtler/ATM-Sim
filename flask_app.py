
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, url_for, request, redirect, Response
import sqlite3
import shortuuid
from flask_sslify import SSLify
from functools import wraps


app = Flask(__name__)
sslify = SSLify(app)

@app.route('/save/<attempt>')
def save(attempt):
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    c.execute('INSERT INTO attempts VALUES (?)', (attempt,))
    conn.commit()
    conn.close()
    return attempt

@app.route('/create_db')
def setup():
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    #c.execute('DROP TABLE IF EXISTS attempts')
    c.execute('CREATE TABLE attempts (attempt)')
    #c.execute('DROP TABLE IF EXISTS passwords')
    #c.execute('CREATE TABLE passwords (password)')
    #c.execute('DROP TABLE IF EXISTS uids')
    c.execute('CREATE TABLE uids (uid, email)') # uid, email, password
    conn.commit()
    conn.close()
    return "OK"

'''
@app.route('/reset_attempts')
def reset():
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS attempts')
    c.execute('CREATE TABLE attempts (attempt)')
    conn.commit()
    conn.close()
    return "OK"
'''

@app.route('/over')
def over():
    return render_template('over.html')

@app.route('/get_uid', methods=['GET', 'POST'])
def get_uid():
    result = ''
    vars = ''
    if request.method == 'POST':
        email = request.form['email']
        conn = sqlite3.connect('attempts.db')
        c = conn.cursor()
        c.execute('SELECT uid FROM uids where email=?', (email,))
        res = c.fetchone()
        if res:
            vars = res[0]
        else:
            uid = shortuuid.uuid()[:5]
            #c.execute('SELECT password FROM passwords LIMIT 1')
            #password = c.fetchone()
            #c.execute('DELETE FROM passwords WHERE password=?', (password))
            c.execute('INSERT INTO uids VALUES (?,?)', (uid, email))
            conn.commit()
            vars = uid
        result = 'Your URL to access the experiment is <a href=".{}">dantt.pythonanywhere.com{}</a>'.format(url_for('experiment', uid=vars), url_for('experiment', uid=vars))
        conn.close()
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

@app.route('/download')
@requires_auth
def download():
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM attempts')
    res = c.fetchall()
    conn.close()
    return str(res)

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
