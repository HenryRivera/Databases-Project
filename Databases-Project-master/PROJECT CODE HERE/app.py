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
                             password="",
                             db="finsta_db",
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
  
  
@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")
  
  
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

  
# CODE FOR LOGIN
@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

  
# CODE FOR LOGIN
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
  
  
# CODE FOR VIEW VISIBLE PHOTOS AND VIEW FURTHER PHOTO INFO
@app.route('/images', methods=["GET"])
@login_required
def images():
    username = session["username"]
    # get the users information
    cursor = connection.cursor()
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    firstName = data["firstName"]
    lastName = data["lastName"]
    # get the photos visible to the username
    query = 'SELECT photoID,postingdate,filepath,caption,photoPoster FROM Photo WHERE photoPoster = %s OR photoID IN ' \
            '(SELECT photoID FROM Photo WHERE photoPoster != %s AND allFollowers = 1 AND photoPoster IN ' \
            '(SELECT username_followed FROM Follow WHERE username_follower = %s AND username_followed = photoPoster AND followstatus = 1)) OR photoID IN ' \
            '(SELECT photoID FROM SharedWith NATURAL JOIN BelongTo NATURAL JOIN Photo WHERE member_username = %s AND photoPoster != %s) ORDER BY postingdate DESC'
    cursor.execute(query, (username, username, username, username, username))
    data = cursor.fetchall()
    for post in data:  # post is a dictionary within a list of dictionaries for all the photos
        query = 'SELECT username, firstName, lastName FROM Tagged NATURAL JOIN Person WHERE tagstatus = 1 AND photoID = %s'
        cursor.execute(query, (post['photoID']))
        result = cursor.fetchall()
        # print('hello')
        if result:
            post['tagees'] = result
        query = 'SELECT firstName, lastName FROM Person WHERE username = %s'
        cursor.execute(query, (post['photoPoster']))
        ownerInfo = cursor.fetchone()
        post['firstName'] = ownerInfo['firstName']
        post['lastName'] = ownerInfo['lastName']

    cursor.close()
    return render_template('images.html', images=data, firstName=firstName, lastName=lastName)


@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")


# CODE FOR POST A PHOTO
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
  
  
# CODE FOR POST A PHOTO
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
            updateShared = "INSERT INTO SharedWith (groupOwner, groupName, photoID) VALUES (%s, %s, %s)"
            with connection.cursor() as cursor:
                cursor.execute(groupQuery, username)
            groups = cursor.fetchall()

            for group in groups:
                if (request.form.get(group["groupName"]) == group["owner_username"]):
                    with connection.cursor() as cursor:
                        cursor.execute(updateShared, (group["owner_username"], group["groupName"], insertedPhotoID))
        
        message = "Image has been successfully uploaded."
        return render_template("upload.html", message=message)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)
      
      
# CODE FOR MANAGE FOLLOWS PART A
@app.route("/follow", methods=["GET", "POST"])
@login_required
def follow():
    if request.form:
        username = request.form['username']
        cursor = connection.cursor()
        query = 'SELECT * FROM person WHERE username = %s'
        cursor.execute(query, (username))
        data = cursor.fetchone()

        if data:  # if there is username with given "username"
            query = "SELECT * FROM follow WHERE username_followed = %s AND username_follower = %s"
            cursor.execute(query, (username, session['username']))
            data = cursor.fetchone()
            if (data):
                if (data["followstatus"] == 1):
                    error = "Already following user"
                else:
                    error = "Request is still pending"
                return render_template("follow.html", message=error)
            else:
                query = "INSERT INTO follow VALUES(%s, %s, 0)"
                connection.commit()
                cursor.execute(query, (username, session['username']))
                message = "Follow Request Successful!"
                return render_template("follow.html", message=message)
        else:
            # returns an error message to the html page
            error = 'Invalid username'
        cursor.close()
        return render_template('follow.html', message=error)
    return render_template('follow.html')

  
# CODE FOR MANAGE FOLLOWS PART B
@app.route("/manageRequests", methods=["GET", "POST"])
@login_required
def manageRequests():
    # get all the requests that have followstatus = 0 for the current user
    cursor = connection.cursor()
    query = "SELECT username_follower FROM follow WHERE username_followed = %s"
    cursor.execute(query, (session["username"]))
    data = cursor.fetchall()
    if request.form:
        pass
        # handle form goes here
    cursor.close()
    return render_template("manageRequests.html", followers=data)
  
  
# CODE FOR LIKE PHOTO
@app.route("/likeImage", methods=["POST"])
@login_required
def like_image():
    username = session["username"]
    query = "INSERT IGNORE INTO Likes (username, photoID, liketime) values (%s, %s, %s)"
    pID = request.form["photoID"]
    # print(pID) -- making sure jquery is sending correct value
    with conection.cursor() as cursor:
        cursor.execute(query,(username, pID, time.strftime('%Y-%m-%d %H:%M:%S')))
    return render_template("images.html")
  
  
# CODE FOR SEARCH BY POSTER
@app.route("/searchPoster", methods=["GET"])
def searchPoster():
    return render_template("searchPoster.html")

  
# CODE FOR SEARCH BY POSTER
@app.route("/searchAuth", methods=["POST"])
def searchAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]

        with connection.cursor() as cursor:
            query = "SELECT * FROM Photo WHERE photoPoster = %s"
            cursor.execute(query, username)
        data = cursor.fetchall()
        if data:
            session["username"] = username
            return render_template("images.html", username=username, images=data)
        error = username + " does not have any posts."
        return render_template("searchPoster.html", error=error)
    error = "An unknown error has occurred. Please try again."
    return render_template("searchPoster.html", error=error)
  
  
# CODE FOR ADD FRIENDGROUP
@app.route("/registerFriendGroup", methods=["GET"])
def registerFriendGroup():
    return render_template("registerFriendGroup.html")
  
  
# CODE FOR ADD FRIENDGROUP
@app.route("/registerAuthFG", methods=["POST"])
def registerAuthFG():
    username = session["username"]
    if request.form:
        requestData = request.form
        groupName = requestData["groupName"]
        description = requestData["description"]

        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO Friendgroup (groupOwner, groupName, description) VALUES (%s, %s, %s)"
                cursor.execute(query, (username, groupName, description))
                query = "INSERT INTO BelongTo (member_username, owner_username, groupName) VALUES (%s, %s, %s)"
                cursor.execute(query, (username, username, groupName))
        except pymysql.err.IntegrityError:
            error = "%s already exists." % groupName
            return render_template('registerFriendGroup.html', error=error)
        return redirect(url_for("home"))

    error = "An error has occurred. Please try again."
    return render_template("registerFriendGroup.html", error=error)
  
  
# CODE FOR ADD FRIEND  
@app.route("/groups")
@login_required
def friend_groups():
    username = session["username"]
    query = "SELECT DISTINCT owner_username, groupName FROM BelongTo WHERE member_username = %s OR owner_username = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (username, username))
    data = cursor.fetchall()

    return render_template("groups.html", groups=data)

  
# CODE FOR ADD FRIEND
@app.route("/addToGroup", methods=["POST"])
@login_required
def add_user():
    username = session["username"]
    userToAdd = request.form["userToAdd"] # need to check if user exists
    groups = request.form.getlist("groups[]")
    # print(groups)
    userQuery = "SELECT * FROM Person WHERE username = %s"
    addToQuery = "INSERT INTO BelongTo VALUES (%s, %s, %s)"
    with connection.cursor() as cursor:
        cursor.execute(userQuery, userToAdd)
    data = cursor.fetchone()
    if (data is None):
        print("debugging user not found functionality")
        message = "User could not be added to selected group - Check if user exists"
        return message
        #return render_template("groups.html", message=message)
    else:
        try:
            print("trying")
            with connection.cursor() as cursor:
                cursor.execute(addToQuery, (userToAdd, username, groups[0]))
            message = "User successfully added to selected group"
            return message
            #return render_template("groups.html", message=message)
        except:
            print("except")
            message = "User could not be added to selected group - Already a member"
            return message
            #return render_template("groups.html", message=message)


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username")
    return redirect("/")


if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run()
