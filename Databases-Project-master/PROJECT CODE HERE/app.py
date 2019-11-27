from flask import Flask, render_template, request, session, redirect, url_for, send_file
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time

SALT = "cs3083"

app = Flask(__name__)
app.secret_key = "super secret key"
IMAGES_DIR = os.path.join(os.getcwd(), "images")

connection = pymysql.connect(host="localhost",
                             user="root",
                             password="%001001%",
                             db="finsta",
                             charset="utf8mb4",
                             port=3306,
                             cursorclass=pymysql.cursors.DictCursor,
                             autocommit=True)


def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return dec


@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")


@app.route("/home")
@login_required
def home():
    return render_template("home.html", username=session["username"])


@app.route("/upload", methods=["GET"])
@login_required
def upload():
    username=session["username"]
    # need a query to display all friend groups the user belongs to
    query = "SELECT groupName, owner_username from BelongTo WHERE member_username = %s"
    # ownedQuery = "SELECT groupName FROM Friendgroup WHERE groupOwner = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, username)
    data = cursor.fetchall()
    
    #with connection.cursor() as cursor:
    #    cursor.execute(ownedQuery, username)
    #groupsOwned = cursor.fetchall()
    return render_template("upload.html", groupNames=data)


@app.route("/images", methods=["GET"])
@login_required
def images():
    query = "SELECT * FROM Photo"
    with connection.cursor() as cursor:
        cursor.execute(query)
    data = cursor.fetchall()
    return render_template("images.html", images=data)


@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")


@app.route("/loginAuth", methods=["POST"])
def loginAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"] + SALT
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()

        with connection.cursor() as cursor:
            query = "SELECT * FROM Person WHERE username = %s AND password = %s"
            cursor.execute(query, (username, hashedPassword))
        data = cursor.fetchone()
        if data:
            session["username"] = username
            return redirect(url_for("home"))

        error = "Incorrect username or password."
        return render_template("login.html", error=error)

    error = "An unknown error has occurred. Please try again."
    return render_template("login.html", error=error)


@app.route("/registerAuth", methods=["POST"])
def registerAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"] + SALT
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
        firstName = requestData["fname"]
        lastName = requestData["lname"]
        bio = requestData["bio"]

        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO Person (username, password, firstName, lastName, bio) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (username, hashedPassword, firstName, lastName, bio))
        except pymysql.err.IntegrityError:
            error = "%s is already taken." % (username)
            return render_template('register.html', error=error)

        return redirect(url_for("login"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username")
    return redirect("/")


@app.route("/uploadImage", methods=["POST"])
@login_required
def upload_image():
    # for future use
    allFollowers = 0

    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        #print(image_name)
        filepath = os.path.join(IMAGES_DIR, image_name)
        # print(filepath)
        image_file.save(filepath)
        username = session["username"]

        whoCanView = request.form.get("who")

        # for future use of setting allFollowers
        # if it is false, we want to add it to the specified friend groups
        if (whoCanView == "allFollowers"):
            allFollowers = 1
    
        # add the photo to the photo table
        query = "INSERT INTO Photo (postingdate, filepath, allFollowers, photoPoster) VALUES (%s, %s, %s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'), filepath, allFollowers, username))
        insertedPhotoID = cursor.lastrowid
        
        # we need to update the SharedWith table if allFollowers was not selected
        if (not allFollowers):
            groupQuery = "SELECT owner_username, groupName from BelongTo WHERE member_username = %s"
            #ownedQuery = "SELECT groupOwner, groupName FROM Friendgroup WHERE groupOwner = %s"
            updateShared = "INSERT INTO SharedWith (groupOwner, groupName, photoID) VALUES (%s, %s, %s)"
            with connection.cursor() as cursor:
                cursor.execute(groupQuery, username)
            groups = cursor.fetchall()

            #with connection.cursor() as cursor:
            #    cursor.execute(ownedQuery, username)
            #groupsOwned = cursor.fetchall()
            
            #try:
            #    groups = memberOf + groupsOwned
            #except:
            #    groups = groupsOwned
            for group in groups:
                if (request.form.get(group["groupName"]) == group["owner_username"]):
                    with connection.cursor() as cursor:
                        cursor.execute(updateShared, (group["owner_username"], group["groupName"], insertedPhotoID))
        
        message = "Image has been successfully uploaded."
        return render_template("upload.html", message=message)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)


if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run()
