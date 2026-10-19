#Sources:
#CSRFProtection:
#https://flask-wtf.readthedocs.io/en/latest/csrf/

#Database:
#https://www.geeksforgeeks.org/python/flask-app-configuation/app

#Input Validation / Enumeration:
#https://www.zerobounce.net/email-guides/python-email-verification

#Password Policies
#CSPRNG: https://docs.python.org/3/library/secrets.html
#https://www.geeksforgeeks.org/python/create-a-random-password-generator-using-python/
#https://stackoverflow.com/questions/9264033/how-to-insert-value-in-input-with-javascript
#https://bitwarden.com/passphrase-generator/
#https://codereview.stackexchange.com/questions/216128/generate-eff-diceware-passwords-with-python
#https://www.geeksforgeeks.org/python/secrets-python-module-generate-secure-random-numbers/

#Disabling Cache / hiding sensitive data
#https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

import re, io, re, string, pyotp, qrcode, requests, os, base64, werkzeug, gunicorn, secrets
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from datetime import timedelta, datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

load_dotenv(override=True)

app = Flask(__name__, template_folder='templates')

#Prevents user from clicking the Back button on the browser to see previous, sensitive information (Disables cache)
@app.after_request
def add_headers(response):
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store, no-cache" 
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

csrf = CSRFProtect(app) #Used to prove the user is real and not a bot.
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT'))
app.config["MYSQL_CHARSET"] = os.getenv("MYSQL_CHARSET") 
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
app.secret_key = os.getenv("SECRET_KEY") 
mysql = MySQL(app)

app.config["RATELIMIT_ENABLED"] = False
rateLimiter = Limiter(get_remote_address, app=app, storage_uri = "memory://")
f = Fernet(os.getenv("TOTP_ENCRYPTION_KEY").encode())

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# #
# FUNCTIONS FOR VALIDATIONS (NOTE: MOVE TO SEPARATE .py LATER ON)
# #

# #
# PASSWORD / PASSPHRASE GENERATOR (NIST SP800-63B-4 GUIDELINES) (no complexity guidelines, minimum 15 characters, maximum 128 characters and CSPRNG numbers/word choice)
# #  


#Grabs all of the words from the eff 2016 wordlist to turn into passphrases
wordlist = []
with open("data/eff_large_wordlist.txt") as eff:
    for line in eff:
        if line.strip() != "":
            num, phrase = line.split()
            wordlist.append(phrase)

upperChar = string.ascii_uppercase
lowerChar = string.ascii_lowercase
digits = string.digits
symbols = "#@!%$&^*()?_"


def generatePassphrase(wordCount, capitalize, number):
    if wordCount < 5:
        wordCount = 5
    if wordCount > 10:
        wordCount = 10

    words = []
    for _ in range(wordCount):
        word = secrets.choice(wordlist)
        if capitalize:
            word = word.capitalize()

        words.append(word)

    #Adds a number to the end of a random word
    if number:
        index = secrets.randbelow(len(words))
        words[index] = words[index] + secrets.choice(digits)
    

    return "-".join(words)
    

def generatePassword(length, upperChar, lowerChar, digits, symbols):
    if length < 15:
        length = 15
    if length > 128:
        length = 128


    password = ""

    if upperChar:
        password = password+string.ascii_uppercase

    if lowerChar:
        password = password+string.ascii_lowercase

    if digits:
        password = password+string.digits

    if symbols: 
        password = password+"#@!%$&^*()?_"

    if password == "":
        password = string.ascii_letters

    return "".join(secrets.choice(password) for _ in range (length))








@app.route("/")
def home():
    return render_template("landing_page.html")


# #
#  USER AUTHENTICATION (REGISTER, LOGIN, PASSWORD GENERATOR)
# #

@app.route("/password_generator")
def password_generator():

    #Used to display a specific generator
    mode = request.args.get("mode")
    if mode != "passphrase":
        mode = "password"
    return render_template("password_generator.html", mode = mode)

@app.route("/generate", methods=["POST"])
def generate():
    mode = request.form["mode"]
    if mode != "passphrase":
        mode = "password"

    upperChar = request.form.get("upperChar")
    lowerChar = request.form.get("lowerChar")
    digits = request.form.get("digits")
    symbols = request.form.get("symbols")
    capitalize = request.form.get("capitalize")
    number = request.form.get("number")


    if mode == "password":
        length = int(request.form["length"])
        password = generatePassword(length, upperChar, lowerChar, digits, symbols)

    else:
        words = int(request.form["words"])
        password = generatePassphrase(words, capitalize, number)

    #x = x is used to keep persistent checkbox marked via jinja template
    return render_template("password_generator.html", password=password, mode=mode, upperChar=upperChar, lowerChar=lowerChar, digits=digits, symbols=symbols, capitalize=capitalize, number=number) 





#makes it so that it only runs the app when executed
if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0", port=5000)