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

#Rate Limiting
#https://flask-limiter.readthedocs.io/en/stable/
#https://flask-limiter.readthedocs.io/en/stable/api.html#flask_limiter.Limiter.params.key_func Suggestions for limits

#Forgot / Reset Password
#https://medium.com/@khalidnoori568/how-to-build-a-password-reset-email-system-in-python-step-by-step-guide-2ec4d89eaad3

#Password Generator
#Joining strings https://stackoverflow.com/questions/3854692/generate-password-in-python

#Register / Login Forms
#Register https://www.geeksforgeeks.org/python/login-and-registration-project-using-flask-and-mysql/
#Blocklist for commonly breached passwords (NIST): https://github.com/vlhomme/list-of-most-common-password/blob/master/passwords.json

#Two Factor Authentication
#https://www.freecodecamp.org/news/how-to-implement-two-factor-authentication-in-your-flask-app/
#Retrieve latest user id for 2FA verification https://stackoverflow.com/questions/26782746/how-to-get-the-last-row-id-on-update
#Recovery codes / expiring 2FA verification https://dev.to/ayinedjimi-consultants/implementing-totp-two-factor-authentication-from-scratch-in-python-4j9 + https://stackoverflow.com/questions/53443959/set-a-python-program-to-expire-after-a-certain-number-of-days
#Counting remaining rows https://stackoverflow.com/questions/68534871/counting-all-records-in-table-and-putting-it-into-a-variable-inside-mysql-itself
#Guidelines RFC 6238 https://www.rfc-editor.org/info/rfc6238/

#Exception Handling
# CSRF Errors https://flask-wtf.readthedocs.io/en/latest/csrf/

import re, io, re, string, pyotp, qrcode, requests, os, base64, werkzeug, gunicorn, secrets, time
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_wtf.csrf import CSRFProtect, CSRFError
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

app.config["RATELIMIT_ENABLED"] = False #NOTE: TURN ON WHEN TESTING
rateLimiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    
)

f = Fernet(os.getenv("TOTP_ENCRYPTION_KEY").encode()) #Uses a base64 encoded, 32 byte key from environment variables


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







# - - - - - - - - - - 
# FUNCTIONS FOR FEATURES (ORDER: Generate 2FA Recovery Codes, Use recovery code, Validation + Encryption Functions, Exception Handling Functions, Password / Passphrase Generator) (NOTE: MOVE TO SEPARATE .py LATER ON) 
# - - - - - - - - - - 

# #
#  2FA RECOVERY CODES
# #
codeCombination = string.ascii_uppercase+string.digits

#Generates 8 recovery codes in the format XXXX-XXXX, which are then hashed and stored in the respective user's recovery codes table
def generateRecoveryCodes(userId):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM recovery_codes WHERE user_id = %s", (userId,)) #Reset existing codes for new ones
    codes = []
    for _ in range(8):
        codeFormat = "".join(secrets.choice(codeCombination) for _ in range (8))
        code = codeFormat[:4] + "-" + codeFormat[4:] #adds in a hyphen in the middle of the codes 
        codes.append(code)
        cursor.execute("INSERT INTO recovery_codes (user_id, code_hash) VALUES (%s, %s)", (userId, generate_password_hash(code))) #Hash codes with scrypt with a salt of 16
    cursor.close()
    return codes


#Single use recovery code
def useRecoveryCode(userId, code):
    #Accepts formats: XXXX-XXXX, xxxx-xxxx, XXXX XXXX and xxxx xxxx
    normalisation = code.replace("-", "").replace(" ", "").upper()

    if len(normalisation) != 8:
        return False
    
    correctCode = normalisation[:4] + "-" + normalisation[4:]

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, code_hash FROM recovery_codes WHERE user_id = %s", (userId,))
    rows = cursor.fetchall()

    for row in rows:
        if check_password_hash(row["code_hash"], correctCode):
            cursor.execute("DELETE FROM recovery_codes WHERE id = %s", (row["id"],))
            mysql.connection.commit()
            cursor.close()
            return correctCode, len(rows)-1
        
    cursor.close()
    return False


# #
# VALIDATION + ENCRYPTION FUNCTIONS
# # 
#2FA Encryption (encrypted via AES-128)
def encrypt2fa(plaintext):
    return f.encrypt(plaintext.encode()).decode()

def decrypt2fa(ciphertext):
    return f.decrypt(ciphertext.encode()).decode()

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
def isPasswordValid(password):
    if len(password) < 15 or len(password) > 128:
            return False

    
    with open("data/passwords.txt", encoding="utf-8", errors="ignore") as textFile:
        for line in textFile:
            if line.strip().lower() == password.lower():
                return "breached"

    return True


# #
# EXCEPTION HANDLING FUNCTIONS 
# # 

#NOTE: ADD IN CODE 403 FOR ROLE NOT PERMITTED WHEN DOING RBAC
#NOTE 2: MAKE DELETE ACCOUNT CHECK FOR USER ROLE IF THEY ARE ADMIN

#Exceeding rate limit: 429 Too Many Requests
@app.errorhandler(werkzeug.exceptions.TooManyRequests)
def handle_rate_limit(e):
    flash(e.description, "warning")
    return "429 Too Many Requests, try again later",429

#404 Page not found
@app.errorhandler(werkzeug.exceptions.NotFound)
def handle_notfound_request(e):
    flash(e.description, "warning")
    return "404 Page Not Found",404


#500 Internal Server Error
@app.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_server_error(e):
   flash(e.description, "warning")
   return "500 Internal Server Error",500


#Catch bad requests / CSRF errors
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash(e.description, "warning")
    return redirect(request.referrer)

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











# - - - - - - - - - - 
# FUNCTIONALITY OF THE PROJECT
# - - - - - - - - - - 

# - - - - - - - - - - 
#  USER AUTHENTICATION (ORDER: Register, 2FA Verification, Login, 2FA Login, 2FA Recovery Codes)
# - - - - - - - - - -

@app.route("/register", methods=["GET", "POST"])
@rateLimiter.limit("5 per minute; 20 per hour", methods=["POST"])
def register():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    elif request.method == "GET":
        return render_template("register.html")

    username = request.form["username"].strip()
    password = request.form["password"]
    email = request.form["email"].strip().lower()
    hashPass = generate_password_hash(password)

    if isPasswordValid(password) == "breached":
        flash("Password is commonly breached, try again", "danger")
        return render_template("register.html", email=email, username=username)

    if usernameExists(username) or not validEmail(email) or emailExists(email) or isPasswordValid(password) == False or len(username) > 50 or len(username) < 3:
        flash("Error, try again", "danger")
        return render_template("register.html", email=email, username=username)



    else:
        secret = pyotp.random_base32()
        encryptSecret = encrypt2fa(secret) 
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (username, email, hashed_password, twofa_confirmed, twofa_secret) VALUES (%s, %s, %s, 0, %s)", (username, email, hashPass,encryptSecret))
        mysql.connection.commit()
        pendingId = cursor.lastrowid 
        cursor.close()

        #Creating Temporary details used to identify the user and confirm 2FA TOTP code, but not allow them into the dashboard.
        session.clear()
        session["pending_user_id"] = pendingId
        session["expiry"] = (datetime.now()+timedelta(minutes=15)).timestamp() #Gives the user 15 minutes to activate 2FA before expiring the session.

        return redirect(url_for("register_2fa")) #/register/2fa


@app.route("/register/2fa", methods = ["GET", "POST"])
@rateLimiter.limit("5 per minute; 20 per hour", methods=["POST"])
def register_2fa():
    if datetime.now().timestamp() > session.get("expiry",0):
        session.clear()
        flash("Expiration time run out, you can login in with your details but you still have to activate 2FA", "warning")
        return redirect(url_for("login"))

    

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, email, twofa_confirmed, twofa_secret FROM users WHERE id = %s", (session["pending_user_id"],))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        session.clear()
        return redirect(url_for("login"))

    #If user trys to access this page with 2FA already enabled
    if user["twofa_confirmed"] == 1:
        cursor.close()
        return redirect(url_for("login_2fa")) #/login/2fa

    secret = decrypt2fa(user["twofa_secret"])

    if request.method == "POST":
        if pyotp.TOTP(secret).verify(request.form["code"]):
            cursor.execute("UPDATE users set twofa_confirmed = 1 WHERE id = %s", (user["id"],))
            codes = generateRecoveryCodes(user["id"])
            mysql.connection.commit()
            cursor.close()
            session.clear()
            flash("Account created. Make sure to save these recovery codes incase you lose your 2FA device. These codes are single use.", "success")
            return render_template("recovery_codes.html", codes=codes) 
        flash("Invalid code. Try again", "danger")

    cursor.close()

    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user["email"], issuer_name="DontHackMe")
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render_template("register_2fa.html", qr_code=qr_b64, secret=secret) 


@app.route("/login", methods=["GET", "POST"])
@rateLimiter.limit("5 per minute; 30 per hour", methods=["POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "GET":
        return render_template("login.html")

    

    email = request.form["email"].strip()
    password = request.form["password"]

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email,hashed_password,id,twofa_confirmed,twofa_secret from users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()

    if not user or not check_password_hash(user["hashed_password"], password):
        flash("Invalid email or password, please try again", "danger")
        return render_template("login.html")

    #Redirect to 2FA when details are correct, then assign temporary details to assign identity to the user, but not allow access to the page.
    session.clear()
    session["pending_user_id"] = user["id"]

    #If register was abandoned at the QR code, redo the process to make them verify 2FA again.
    if user["twofa_confirmed"] == 0:
        session.clear()
        session["pending_user_id"] = user["id"]
        session["expiry"] = (datetime.now()+timedelta(minutes=15)).timestamp() #Gives the user 15 minutes to activate 2FA before expiring the session.
        return redirect(url_for("register_2fa")) #/register/2fa

    return render_template("login_2fa.html")

@app.route("/login/2fa", methods=["GET", "POST"])
@rateLimiter.limit("5 per minute; 20 per hour", methods=["POST"])
def login_2fa():

    if "pending_user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT username,email,hashed_password,id,twofa_confirmed,twofa_secret FROM users where id = %s", (session["pending_user_id"],))
        user = cursor.fetchone()
        cursor.close()
        secret = decrypt2fa(user["twofa_secret"])

        #Compares form input to TOTP authenticator code
        if user and user["twofa_confirmed"] == 1 and pyotp.TOTP(secret).verify(request.form["code"]):
            session.clear()
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session["username"] = user["username"]
            session.permanent = True

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT password_reset_at FROM users WHERE id = %s", (user["id"],))
            row = cursor.fetchone()
            cursor.close()

            if row and row["password_reset_at"]:
                flash("Your password was last reset on " + row["password_reset_at"].strftime("%Y-%m-%d %H:%M:%S") + ". If this was not you, please reset your password immediately.", "warning")

            return redirect(url_for("dashboard"))

        flash("Invalid code", "danger")

    return render_template("login_2fa.html")




# - - - - - - - - - - 
#  USER MANAGEMENT (ORDER: Profile, regenerate Recovery Codes, delete account, reactivate 2fa verify+confirm, Password/Passphrase generator, Recovery Code, Forgot Password, Reset Password, Logout)
# - - - - - - - - - -
@app.route("/profile", methods=["GET", "POST"])
@rateLimiter.limit("10 per hour", methods=["POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT username,email, hashed_password FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        currentPassword = request.form["currentPassword"]
        password = request.form["password"]
        confirmPassword = request.form["confirmPassword"]

        if len(username) > 50 or len(username) < 3 or not validEmail(email) or len(email) > 255:
            flash("Invalid username or email", "danger")
            return render_template("profile.html", username=user["username"], email=user["email"])

        if not check_password_hash(user["hashed_password"], currentPassword):
            flash("Incorrect current password", "danger")
            return render_template("profile.html", username=user["username"], email=user["email"])

        if username == user["username"] and email == user["email"] and not password:
            flash("No changes made", "info")
            return render_template("profile.html", username=user["username"], email=user["email"])

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM users WHERE (username = %s OR email = %s) AND id != %s", (username, email, session["user_id"]))
        existingUser = cursor.fetchone()
        cursor.close()
    

        if existingUser:
            flash("Username or email already exists", "danger")
            return render_template("profile.html", username=user["username"], email=user["email"])

        
        #Runs if the user wants to reset password
        if password:
            if password != confirmPassword:
                flash("Passwords do not match", "danger")
                return render_template("profile.html", username=user["username"], email=user["email"])

            if isPasswordValid(password) == "breached":
                flash("Password is commonly breached, try again", "danger")
                return render_template("profile.html", username=user["username"], email=user["email"])

            if isPasswordValid(password) == False:
                flash("Error, try again", "danger")
                return render_template("profile.html", username=user["username"], email=user["email"])

            if check_password_hash(user["hashed_password"], password):
                flash("New password cannot be the same as the old password", "danger")
                return render_template("profile.html", username=user["username"], email=user["email"])

        cursor = mysql.connection.cursor()

        #Updates username, email and password if the user wants to reset their password. If not, only updates username and email.
        if password:
            cursor.execute("UPDATE users SET username = %s, email = %s, hashed_password = %s, password_reset_at = NOW() WHERE id = %s", (username, email, generate_password_hash(password), session["user_id"]))
        else:
            cursor.execute("UPDATE users SET username = %s, email = %s WHERE id = %s", (username, email, session["user_id"]))
        mysql.connection.commit()
        cursor.close()
        session["username"] = username
        session["email"] = email

        flash("Profile updated", "success")
        return redirect(url_for("profile"))

    #Allows for username and email to stay in the form fields upon refresh.
    return render_template("profile.html", username=user["username"], email=user["email"])

#Regenerates security codes
@app.route("/profile/regenerateCodes", methods=["POST"])
@rateLimiter.limit("10 per hour")
def regenerateCodes():
    if "user_id" not in session:
        flash("You need to be logged in.", "danger")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT hashed_password FROM users where id = %s", (session["user_id"],))
    user = cursor.fetchone()
    password = request.form["password"]

    if not user or not check_password_hash(user["hashed_password"], password):
        cursor.close()
        flash("Incorrect password", "danger")
        return redirect(url_for("profile"))

    codes = generateRecoveryCodes(session["user_id"])
    mysql.connection.commit()
    cursor.close()

    return render_template("recovery_codes.html", codes=codes)

#Checks all of the user's identifiable information before deleting their account permanently
@app.route("/profile/deleteAccount", methods=["POST"])
@rateLimiter.limit("10 per hour")
def delete_account():
    if "user_id" not in session:
        flash("You need to be logged in.", "danger")
        return redirect(url_for("login"))

    
    password = request.form["password"]
    email = request.form["email"].strip().lower()
    totpCode = request.form["totpCode"].strip()
    recoveryCode = request.form["recoveryCode"].strip()
    confirmText = request.form["confirmText"].strip()
    understand = request.form.get("understand")
    normalisation = recoveryCode.replace("-", "").replace(" ", "").upper() #Accepts code formats: XXXX-XXXX, xxxx-xxxx, XXXX XXXX and xxxx xxxx

    if len(password) > 128 or len(email) > 255 or len(totpCode) > 6 or len(normalisation) > 8:
        flash("Invalid input", "danger")
        return redirect(url_for("profile"))

    correctRecoveryCode = normalisation[:4] + "-" + normalisation[4:]
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, email, hashed_password, twofa_secret FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        session.clear()
        return redirect(url_for("login"))

    cursor.execute("SELECT code_hash FROM recovery_codes WHERE user_id = %s", (session["user_id"],))
    rows = cursor.fetchall()

    #Checks used to verify the user's information
    verifyPassword = check_password_hash(user["hashed_password"], password)
    verifyEmail = user["email"] == email
    verifyTOTP = pyotp.TOTP(decrypt2fa(user["twofa_secret"])).verify(totpCode, valid_window=1) #Allows for a 30 second window before and after the current time to account for clock drift
    verifyRecoveryCode = any(check_password_hash(row["code_hash"], correctRecoveryCode) for row in rows)

    if not (verifyPassword and verifyEmail and verifyTOTP and verifyRecoveryCode and confirmText == "DELETE" and understand == "confirmed"):
        cursor.close()
        flash("Not all fields were valid. Please try again to delete the account.", "danger")
        return redirect(url_for("profile"))

    cursor.execute("DELETE FROM users WHERE id = %s", (session["user_id"],))
    mysql.connection.commit()
    cursor.close()
    session.clear()
    flash("Account deleted successfully", "success")
    return redirect(url_for("home"))


#Re-check the user before allowing them to reactivate 2FA
@app.route("/profile/reactivate2fa", methods=["GET", "POST"])
@rateLimiter.limit("10 per hour", methods=["POST"])
def reactivate2fa():
    if "user_id" not in session:
        flash("You need to be logged in.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form["password"]
        totpCode = request.form["totpCode"].strip()
        recoveryCode = request.form["recoveryCode"].strip()
        normalisation = recoveryCode.replace("-", "").replace(" ", "").upper() #Accepts code formats: XXXX-XXXX, xxxx-xxxx, XXXX XXXX and xxxx xxxx

        if len(password) > 128 or len(totpCode) > 6 or len(normalisation) > 8:
            flash("Invalid input", "danger")
            return redirect(url_for("reactivate2fa"))

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, hashed_password, twofa_secret FROM users WHERE id = %s", (session["user_id"],))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            session.clear()
            return redirect(url_for("login"))

        verifyPassword = check_password_hash(user["hashed_password"], password)
        verifyTOTP = pyotp.TOTP(decrypt2fa(user["twofa_secret"])).verify(totpCode, valid_window=1) #Allows for a 30 second window before and after the current time to account for clock drift
        verifyRecoveryCode = False
        if normalisation:
            correctRecoveryCode = normalisation[:4] + "-" + normalisation[4:]
            cursor.execute("SELECT code_hash FROM recovery_codes WHERE user_id = %s", (session["user_id"],))
            rows = cursor.fetchall()
            verifyRecoveryCode = any(check_password_hash(row["code_hash"], correctRecoveryCode) for row in rows)

        cursor.close()

        #Gives the user the choice of using a TOTP code OR a recovery code 
        if not (verifyPassword and (verifyTOTP or verifyRecoveryCode)):
            flash("Not all fields were valid. Please try again to reactivate 2FA.", "danger")
            return redirect(url_for("reactivate2fa"))

        #Temporary details to identify the user and allow them to reactivate 2FA
        session["temp2FASecret"] = encrypt2fa(pyotp.random_base32())
        session["temp2FAExpiry"] = (datetime.now()+timedelta(minutes=15)).timestamp() #Gives the user 15 minutes to reactivate 2FA before expiring the session.
        return redirect(url_for("reactivate2fa_confirm"))

#Show the new QR code and replace the old secret once  the user proves their identity on the new device
@app.route("/profile/reactivate2fa/confirm", methods=["GET","POST"])
@rateLimiter.limit("10 per hour")
def reactivate2fa_confirm():
    if "user_id" not in session:
        return redirect(url_for("login"))


    if "temp2FASecret" not in session or datetime.now().timestamp() > session.get("temp2FAExpiry",0):
        session.clear()
        flash("Re-activation expired. Current authenticator still works.", "warning")
        return redirect(url_for("profile"))

    secret = decrypt2fa(session["temp2FASecret"])

    if request.method == "POST":
        code = request.form["code"].strip()


        if len(code) == 6 and pyotp.TOTP(secret).verify(code, valid_window=1):
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE users SET twofa_secret = %s WHERE id = %s", (session["temp2FASecret"], session["user_id"])) #Secret is still encrypted
            mysql.connection.commit()
            cursor.close()
            session.clear()
            flash("Authenticator secret updated. Your old authenticator will no longer work, so remove it from your old device (if you still have it)", "success")
            return redirect(url_for("profile"))

        flash("Invalid code. Try again", "danger")


    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user["email"], issuer_name="DontHackMe")
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render_template("reactivate_2fa.html", qr_code=qr_b64, secret=secret)
    


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

#Alternative way to sign into account IF you lose your authenticator
@app.route("/recovery", methods = ["GET", "POST"])
@rateLimiter.limit("5 per minute; 30 per hour", methods=["POST"])
def recovery():
    userId = session.get("pending_user_id")

    if userId is None:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("recovery.html")

    result =  useRecoveryCode(userId, request.form["code"])
    
    if result:
        code, remaining = result #Assigns correctCode and remaining rows left
        session.clear()
        session["user_id"] = userId
        session.permanent = True
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT password_reset_at FROM users WHERE id = %s", (session["user_id"],))
        row = cursor.fetchone()
        cursor.close()
        if row and row["password_reset_at"]:
            flash("Your password was last reset on " + row["password_reset_at"].strftime("%Y-%m-%d %H:%M:%S") + ". If this was not you, please reset your password immediately.", "warning")

        flash(f"Recovery code {code} has been used. {remaining} codes remaining.", "success")
        return redirect(url_for("dashboard"))

    
    flash("Invalid recovery code", "danger")
    return render_template("recovery.html")


@app.route("/forgot-password", methods = ["GET", "POST"])
@rateLimiter.limit("5 per minute; 10 per hour", methods=["POST"])
def forgot_password():
    if request.method == "POST":
        details = request.form["details"].strip().lower()
        totpCode = request.form["totpCode"].strip()
        recoveryCode = request.form["recoveryCode"].strip()
        normalisation = recoveryCode.replace("-", "").replace(" ", "").upper() #Accepts code formats: XXXX-XXXX, xxxx-xxxx, XXXX XXXX and xxxx xxxx

        if len(details) > 255 or len(totpCode) > 6 or len(normalisation) > 8:
            flash("Invalid input", "danger")
            return render_template("forgot_password.html")

        correctCode = normalisation[:4] + "-" + normalisation[4:]
        cursor = mysql.connection.cursor()

        #Used to differentiate if the user chose their email or username to identify themselves
        if "@" in details:
            cursor.execute("SELECT id, twofa_secret FROM users WHERE email = %s", (details,))
        else:
            cursor.execute("SELECT id, twofa_secret FROM users WHERE username = %s", (details,))
        user = cursor.fetchone()
        cursor.close()

    
        if user:
            totpVerify = pyotp.TOTP(decrypt2fa(user["twofa_secret"])).verify(totpCode, valid_window=1) #Allows for a 30 second window before and after the current time to account for clock drift
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id,code_hash FROM recovery_codes WHERE user_id = %s", (user["id"],))
            rows = cursor.fetchall()
            cursor.close()

            recoveryVerify = any(check_password_hash(row["code_hash"], correctCode) for row in rows)

            #Allows user to reset password if TOTP and recovery code are valid
            #Provide temporary details to identify the user and allow them to reset their password, but not allow access to the dashboard.
            if totpVerify and recoveryVerify:
                session.clear()
                session["reset_user_id"] = user["id"]
                session["resetExpiry"] = (datetime.now()+timedelta(minutes=5)).timestamp() 
                return redirect(url_for("reset_password"))
            
        flash("TOTP or recovery code is invalid", "danger")

    return render_template("forgot_password.html")

@app.route("/reset-password", methods = ["GET", "POST"])
@rateLimiter.limit("10 per hour", methods=["POST"])
def reset_password():
    #Send user back to forgot password if session expired or they try to access the page without going through the forgot password process
    if "reset_user_id" not in session or datetime.now().timestamp() > session.get("resetExpiry",0):
        session.clear()
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form["password"]
        confirmPassword = request.form["confirmPassword"]
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT hashed_password from users WHERE id = %s", (session["reset_user_id"],))
        user = cursor.fetchone()
        cursor.close()
        if password != confirmPassword:
            flash("Passwords do not match", "danger")
            return render_template("reset_password.html")

        if isPasswordValid(password) == "breached":
            flash("Password is commonly breached, try again", "danger")
            return render_template("reset_password.html")
        
        if isPasswordValid(password) == False:
            flash("Error, try again", "danger")
            return render_template("reset_password.html")

        if check_password_hash(user["hashed_password"], password):
            flash("New password cannot be the same as the old password", "danger")
            return render_template("reset_password.html")
            

        else:
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE users SET hashed_password = %s, password_reset_at = NOW() WHERE id = %s", (generate_password_hash(password), session["reset_user_id"]))
            mysql.connection.commit()
            cursor.close()
            session.clear()
            flash("Password reset successfully", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html")
 

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))










# - - - - - - - - - - 
#  CORE FUNCTIONALITY: (ORDER: DASHBOARD, MODULES, TESTS, SCANNER)
# - - - - - - - - - -
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")



#makes it so that it only runs the app when executed
if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0", port=5000)