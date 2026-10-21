#Sources:
#CSRFProtection:
#https://flask-wtf.readthedocs.io/en/latest/csrf/

#Database:
#https://www.geeksforgeeks.org/python/flask-app-configuation/app

#Input Validation / Enumeration:
# OWASP REGEX: https://community.owasp.org/OWASP_Validation_Regex_Repository

#Password Policies
#CSPRNG: https://docs.python.org/3/library/secrets.html
#https://www.geeksforgeeks.org/python/create-a-random-password-generator-using-python/
#https://stackoverflow.com/questions/9264033/how-to-insert-value-in-input-with-javascript
#https://bitwarden.com/passphrase-generator/
#https://codereview.stackexchange.com/questions/216128/generate-eff-diceware-passwords-with-python
#https://www.geeksforgeeks.org/python/secrets-python-module-generate-secure-random-numbers/

#Disabling Cache / hiding sensitive data
#https://stackoverflow.com/questions/34066804/disabling-caching-in-flask


#Register / Login Forms
#Register https://www.geeksforgeeks.org/python/login-and-registration-project-using-flask-and-mysql/
#Blocklist for commonly breached passwords (NIST): https://github.com/vlhomme/list-of-most-common-password/blob/master/passwords.json

#Two Factor Authentication
#https://www.freecodecamp.org/news/how-to-implement-two-factor-authentication-in-your-flask-app/
#Retrieve latest user id for 2FA verification https://stackoverflow.com/questions/26782746/how-to-get-the-last-row-id-on-update
#Recovery codes / expiring 2FA verification https://dev.to/ayinedjimi-consultants/implementing-totp-two-factor-authentication-from-scratch-in-python-4j9


import re, io, re, string, pyotp, qrcode, requests, os, base64, werkzeug, gunicorn, secrets, time
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
csrf = CSRFProtect(app) #Used to prove the user is real and not a bot.
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT'))
app.config["MYSQL_CHARSET"] = os.getenv("MYSQL_CHARSET") 
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = os.getenv("SECRET_KEY") 
mysql = MySQL(app)

app.config["RATELIMIT_ENABLED"] = False
rateLimiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
)

f = Fernet(os.getenv("TOTP_ENCRYPTION_KEY").encode()) 



#Prevents user from clicking the Back button on the browser to see previous, sensitive information (Disables cache)
@app.after_request
def add_headers(response):
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store, no-cache" 
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

#Default route
@app.route("/")
def home():
    return render_template("landing_page.html")




# #
# FUNCTIONS FOR VALIDATIONS / FEATURES (NOTE: MOVE TO SEPARATE .py LATER ON)
# #


# #
# VALIDATION + ENCRYPTION FUNCTIONS
# #

#2FA Encryption
def encrypt2fa(plaintext):
    return f.encrypt(plaintext.encode()).decode()

def decrypt2fa(ciphertext):
    return f.encrypt(ciphertext.encode()).decode()

#Format: mail@domain.com / john.email@domain.com
def validEmail(email):
    return re.match(r'^[a-zA-Z0-9_+&*-]+(?:\.[a-zA-Z0-9_+&*-]+)*@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,7}$', email)

def emailExists(email):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    return user

def usernameExists(username):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    return user

#FOLLOWS NIST SP800-63B-4 (Minimum 15 characters, maximum 128 characters, no commonly breached passwords, no forced complexity)
def failPasswordPolicy(password):
    blocklist = []
    with open("data/passwords.txt") as x:
        for line in x:
            password = line.split()
            blocklist.append(password)
    if password < 15 and password > 128:
        return False

    elif (blocklist.contains(password)):
        return False

    return None

    
      


# #
# EXCEPTION HANDLING FUNCTIONS 
# # 

#Exceeding rate limit
@app.errorhandler(werkzeug.exceptions.TooManyRequests)
def handle_rate_limit(e):
    return "429 Too Many Requests: Too many attempts.", 429
  
@app.errorhandler(werkzeug.exceptions.NotFound)
def handle_notfound_request(e):
    return '404 Page not found', 404

#Catch general errors
@app.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_server_error(e):
   return "500 Internal Server Error: Conflict has occurred.", 500


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











# #
#  USER AUTHENTICATION (ORDER: Password Generator, Register, Login)
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




@app.route("/register", methods=["GET", "POST"])
@rateLimiter.limit("10 per minute")
def register():

    if "user_id" in session:
        flash("You are currently logged in.", "warning")
        return redirect(url_for("dashboard"))

    elif request.method == "GET":
        return render_template("register.html")

    username = request.form["username"].strip()
    password = request.form["password"]
    email = request.form["email"].strip().lower()

    if usernameExists(username) or not validEmail(email) or emailExists(email) or failPasswordPolicy(password) == False:
        flash("Error, try again", "danger")
        return render_template("register.html")


    else:
        secret = pyotp.random_base32()
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (username, email, hashed_password, twofa_confirmed, twofa_secret) VALUES (%s, %s, %s, 0, %s)", (username, email, generate_password_hash(password),encrypt2fa(secret)))
        mysql.connection.commit()
        pendingId = cursor.lastrowid
        cursor.close()

        #Creating pending user details to confirm 2FA TOTP code
        session.clear()
        session["pending_user_id"] = pendingId
        session["pending_at"] = time.time()
        return redirect(url_for("register_2fa"))





#makes it so that it only runs the app when executed
if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0", port=5000)