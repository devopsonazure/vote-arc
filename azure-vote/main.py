from flask import Flask, request, render_template, abort
from flask_wtf.csrf import CSRFProtect
import os
import random
import redis
import socket
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
csrf = CSRFProtect(app)

# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis configurations
redis_server = os.environ['REDIS']

# Redis Connection
try:
    if "REDIS_PWD" in os.environ:
        r = redis.StrictRedis(host=redis_server,
                        port=6379,
                        password=os.environ['REDIS_PWD'])
    else:
        r = redis.Redis(redis_server)
    r.ping()
except redis.ConnectionError:
    exit('Failed to connect to Redis, terminating.')

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
try:
    if not r.get(button1): r.set(button1,0)
    if not r.get(button2): r.set(button2,0)
except redis.RedisError:
    exit('Failed to initialize Redis counters, terminating.')

@app.after_request
def add_security_headers(response):
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':
        try:
            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')            

            # Return index with values
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)
        except redis.RedisError:
            abort(500, 'Failed to retrieve vote counts')

    elif request.method == 'POST':
        # Validate the vote input
        if 'vote' not in request.form:
            abort(400, 'Missing vote parameter')
            
        vote = request.form['vote']
        
        # Only allow valid voting options
        valid_options = [button1, button2, 'reset']
        if vote not in valid_options:
            abort(400, 'Invalid vote value')
            
        if vote == 'reset':
            try:
                # Empty table and return results
                r.set(button1,0)
                r.set(button2,0)
                vote1 = r.get(button1).decode('utf-8')
                vote2 = r.get(button2).decode('utf-8')
                return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)
            except redis.RedisError:
                abort(500, 'Failed to reset vote counts')
        
        else:
            try:
                # Insert vote result into DB
                r.incr(vote,1)
                
                # Get current values
                vote1 = r.get(button1).decode('utf-8')
                vote2 = r.get(button2).decode('utf-8')  
                    
                # Return results
                return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)
            except redis.RedisError:
                abort(500, 'Failed to process vote')

if __name__ == "__main__":
    # Ensure debug mode is off in production
    app.run(host='0.0.0.0', port=80, debug=False)
