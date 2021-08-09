"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""
import os
import uuid
from flask import Flask, render_template, request, redirect, abort, session
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SelectField, PasswordField
from wtforms.validators import NumberRange, DataRequired, Length, InputRequired, EqualTo, Optional, Email
from datetime import datetime, date
from hashlib import md5
from flask_mail import Mail, Message
import pymysql
import cryptography

app = Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'pakcollegeartresources@gmail.com'
app.config['MAIL_PASSWORD'] = 'PCartresources1'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

from __main__ import app
from utils import *

# Form for registering
class registerForm(FlaskForm):
    userName = StringField('Username*:', validators = [InputRequired(message="Your username cannot be blank."), Length(max=20, message="Your input must be between 0 and 20 characters long.")])
    password = PasswordField('Password*:', validators = [InputRequired(message="Your password cannot be blank."), EqualTo('confirm', message="Your passwords do not match."), Length(max=60, message="Your input must be between 0 and 60 characters long.")])
    confirm = PasswordField('Confirm password*:')
    email = StringField('Email address*:', validators = [InputRequired(message="Your email address cannot be blank"), Email(message="Your email address must be valid.")])
    firstName = StringField('First name:', validators = [Length(max=60, message="Your input must be between 0 and 60 characters long.")])
    lastName = StringField('Last name:', validators = [Length(max=60, message="Your input must be between 0 and 60 characters long.")])
    yearLevel = IntegerField('Year level:', default = 9, validators = [NumberRange(min=0, max=13, message="Year level options are only from 0-13. Put 0 if you are a teacher or admin.")])
    tutorGroup = StringField('Tutor group:', validators = [Length(max=4, message="Your tutor group can only be 4 characters.")])
    role = SelectField('Role/Permissions*:', choices=[('Student', 'Student'),('Admin', 'Admin'),('Teacher', 'Teacher')])

# Form for editing a user
class editForm(FlaskForm):
    userName = StringField('Username:', validators = [InputRequired(message="Your username cannot be blank."), Length(max=20, message="Your input must be between 0 and 20 characters long.")])
    email = StringField('Email address:', validators = [InputRequired(message="Your email address cannot be blank"), Email(message="Your email address must be valid.")])
    firstName = StringField('First name:', validators = [Length(max=60, message="Your input must be between 0 and 60 characters long.")])
    lastName = StringField('Last name:', validators = [Length(max=60, message="Your input must be between 0 and 60 characters long.")])
    yearLevel = IntegerField('Year level:', default = 9, validators = [NumberRange(min=9, max=13, message="Year level options are only from 0-13.")])
    tutorGroup = StringField('Tutor group:', validators = [Length(max=4, message="Your tutor group can only be 4 characters.")])
    role = SelectField('Role/Permissions:', choices=[('Student', 'Student'),('Admin', 'Admin'),('Teacher', 'Teacher')])

# Form for resetting a password
class passwordForm(FlaskForm):
    password = PasswordField('Password:', validators = [InputRequired(message="Your password cannot be blank."), EqualTo('confirm', message="Your passwords do not match."), Length(max=60, message="Your input must be between 0 and 60 characters long.")])
    confirm = PasswordField('Confirm password:')

# Checking user account exists when resetting password
@app.route("/resetpassword", methods=["GET", "POST"])
def resetpassword():
    enterID = False
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        connection = create_connection()
        with connection.cursor() as cursor:
            sql  = "SELECT firstName, lastName, userID FROM userstable WHERE userName = %s AND email = %s;"
            vals = (username, email)
            cursor.execute(sql,vals)
            names = cursor.fetchone()
            connection.close()
        if names == None:
            return render_template("resetpassword.html")
        else:
            id = uuid.uuid1()
            msg = Message('Pakuranga College Art Resources - Password reset request', sender = 'pakcollegeartdepartment@gmail.com', recipients = [(email)])
            msg.body = "Hey there " + names["firstName"] + " " + names["lastName"] + ". You have requested a passsword reset for your Pakuranga College Art Department Resources account. ID:" + str(id) + " If you don't recognise this account, feel free to disregard this email."
            mail.send(msg)
            return render_template("enterresetID.html", userID = names["userID"], enterID = True, id = id)
    else:
        return render_template("resetpassword.html")

# Check that the user has received the email with the reset ID
@app.route("/enterresetID", methods=["GET", "POST"])
def enterresetID():
    if request.method == "POST":
        id = request.form["id"]
        userID = request.form["userID"]
        resetID = request.form["resetID"]
        if resetID == id:
            form = registerForm(request.form)
            return render_template("setnewpassword.html", userID = userID, form = form)
        else:
           return render_template("enterresetID.html", sendemail = True, enterID = False)
    else:
        return render_template("enterresetID.html")

# Enters new password
@app.route("/setnewpassword", methods=["GET","POST"])
def setnewpassword():
    form = registerForm(request.form)
    userID = int(request.args["userID"])
    return render_template("setnewpassword.html", form = form)

# Checks and sets new password
@app.route("/performsetnewpassword", methods = ["GET", "POST"])
def performsetnewpassword():
    form = passwordForm(request.form)
    if form.validate():
        password = form.password.data
        password = md5(password.encode()).hexdigest()
        userID = request.form["userID"]
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "UPDATE userstable SET password = %s WHERE userID = %s"
            vals = (password, userID)
            cursor.execute(sql, vals)
            connection.commit()
            connection.close()
        return redirect('/login')
    else:
        return render_template("setnewpassword.html", form = form)

# User borrows or returns resources for self
@app.route('/borrow')
def borrow():
    if session["loggedIn"] == True:
        connection = create_connection()
        with connection.cursor() as cursor:
            sql  = "SELECT resourcestable.resourceID, resourcestable.resourceModel, issuetable.issueID, userstable.userID, userstable.firstName FROM resourcestable\
            LEFT JOIN issuetable ON resourcestable.resourceID = issuetable.resourceID\
            LEFT JOIN userstable ON issuetable.userID = userstable.userID;"
            cursor.execute(sql)
            issues = cursor.fetchall()
            connection.close()
        return render_template("borrowresources.html", issues=issues)
    else:
        pass

# Confirm the user is borrowing the selected resource
@app.route('/confirmborrow', methods=["GET", "POST"])
def confirmborrow():
    resourceID = int(request.args["resourceID"])
    connection = create_connection()
    with connection.cursor() as cursor:
       sql = "SELECT * FROM resourcesTable WHERE resourceID = %s;"
       vals = (resourceID)
       cursor.execute(sql, vals)
       this_resource = cursor.fetchone()
       connection.close()
    return render_template("confirmborrow.html", this_resource = this_resource, date = date)

#Confirms the resource that the user is borrowing
@app.route('/confirmissue', methods=["GET", "POST"])
def confirmissue():
    userID = int(request.args["userID"])
    resourceID = int(request.args["resourceID"])
    connection = create_connection()
    with connection.cursor() as cursor:
       sql = "SELECT * FROM resourcesTable WHERE resourceID = %s;"
       vals = (resourceID)
       cursor.execute(sql, vals)
       this_resource = cursor.fetchone()
       connection.close()
    return render_template("confirmissue.html", this_resource = this_resource)

#Issue a resource out to a user
@app.route('/issueresource', methods = ["GET", "POST"])
def issueresource():
    if session["role"] == "Teacher" or session["role"] == "Admin":
        issueDate = date.today()
        userID = session["userID"]
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT userID, userName, firstName FROM userstable"
            cursor.execute(sql)
            users = cursor.fetchall()
            connection.close()
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT resourcestable.resourceID, resourcestable.resourceModel, issuetable.issueID, userstable.userID, userstable.firstName FROM resourcestable\
            LEFT JOIN issuetable ON resourcestable.resourceID = issuetable.resourceID\
            LEFT JOIN userstable ON issuetable.userID = userstable.userID;"
            cursor.execute(sql)
            issues = cursor.fetchall()
            connection.close()
        return render_template('issueresource.html', issues=issues, users=users)
    else:
        redirect('/')

# A user borrowing a resource for themselves
@app.route('/performBorrow', methods = ["GET", "POST"])
def performBorrow():
   issueDate = date.today()
   userID = session["userID"]
   resourceID = request.args["resourceID"]
   connection = create_connection()
   with connection.cursor() as cursor:
       sql = "INSERT INTO issuetable (userID, issueDate, resourceID) VALUES (%s, %s, %s)"
       vals = (userID, issueDate, resourceID)
       cursor.execute(sql, vals)
       connection.commit()
       connection.close()
       return redirect('/borrow')

# A user issuing a camera for another person
@app.route('/performIssue', methods = ["GET", "POST"])
def performIssue():
   issueDate = date.today()
   selectuser = request.form["selectuser"]
   resourceID = request.form["resourceID"]
   connection = create_connection()
   with connection.cursor() as cursor:
       sql = "INSERT INTO issuetable (userID, issueDate, resourceID) VALUES (%s, %s, %s)"
       vals = (selectuser, issueDate, resourceID)
       cursor.execute(sql, vals)
       connection.commit()
       connection.close()
       return redirect('/issueresource')
   
# Returns a resource that was borrowed
@app.route('/returnissue', methods = ["GET", "POST"])
def returnissue():
    resourceID = int(request.args["resourceID"])
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "DELETE FROM issueTable WHERE resourceID = %s;"
        vals = (resourceID)
        cursor.execute(sql, vals)
        connection.commit()
        connection.close()
    if session["role"] == "Student":
        return redirect('/borrow')
    else:
        return redirect('/issueresource')

# Logs in the user
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        userName = request.form["userName"]
        password = request.form["password"]
        password = md5(password.encode()).hexdigest()
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM userstable WHERE userName = %s AND password = %s"
            vals = (userName, password)
            cursor.execute(sql, vals)
            users = cursor.fetchall()
        connection.close()
        if len(users) == 0:
            #Login failed
            return render_template("login.html")
        else:
            #Login succeeded
            user = users[0]
            session['userName'] = user['userName']
            session['firstName'] = user['firstName']
            session['lastName'] = user['lastName']
            session["loggedIn"] = True
            session["role"] = user['role']
            session['userID'] = user['userID']
            return redirect('/')
    else:
        return render_template("login.html")

# Logs out the user
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

# Displays entire user database
@app.route("/usersdatabase")
def manage_users():
    if session["role"] == "Admin":
        connection = create_connection()
        with connection.cursor() as cursor:
            sql  = "SELECT userID, userName, password, email, firstName, lastName, yearLevel, tutorGroup, role FROM userstable" #LEFT JOIN rolestable ON userstable.rolesID = rolesstable.rolesID;"
            cursor.execute(sql)
            users = cursor.fetchall()
            connection.close()
        return render_template("usersdatabase.html", users = users)
    else:
        return redirect('/')

# Displaying and updating a user's information
@app.route('/edituser')
def edituser():
    if session["role"] == "Admin":
        form = editForm(request.form)
        userID = int(request.args["userID"])
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM userstable WHERE userID = %s;"
            vals = (userID)
            cursor.execute(sql, vals)
            this_user = cursor.fetchone()
            connection.close()
        return render_template("edituser.html", this_user = this_user, form = form)
    else:
        return redirect ('/')

# Perform the user update with updated values from form
@app.route('/performEdit', methods = ["GET", "POST"])
def performEdit():
    form = editForm(request.form)
    userID = request.form["userID"]
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "SELECT * FROM usersTable WHERE userID = %s;"
        vals = (userID)
        cursor.execute(sql, vals)
        this_user = cursor.fetchone()
        connection.close()
    if form.validate():
        userName = form.userName.data
        email = form.email.data
        firstName = form.firstName.data
        lastName = form.lastName.data
        yearLevel = form.yearLevel.data
        tutorGroup = form.tutorGroup.data
        role = form.role.data
        userID = request.form["userID"]
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "UPDATE userstable SET userName = %s, email = %s, firstName = %s, lastName = %s, yearLevel = %s, tutorGroup = %s, role = %s WHERE userID = %s"
            vals = (userName, email, firstName, lastName, yearLevel, tutorGroup, role, userID)
            cursor.execute(sql, vals)
            connection.commit()
            connection.close()
        return redirect('/usersdatabase')
    else:
        return render_template("edituser.html", this_user = this_user, form = form)

# Delete a certain user off the database
@app.route('/deleteuser', methods = ["GET", "POST"])
def deleteuser():
   resourceID = int(request.args["userID"])
   connection = create_connection()
   with connection.cursor() as cursor:
       sql = "DELETE FROM userstable WHERE userID = %s;"
       vals = (resourceID)
       cursor.execute(sql, vals)
       connection.commit()
       connection.close()
   return redirect('/usersdatabase')

# Register page for a new user
@app.route("/register", methods=["GET", "POST"])
def register():
    form = registerForm(request.form)
    if request.method == "POST" and form.validate():
        userName = form.userName.data
        password = form.password.data
        password = md5(password.encode()).hexdigest()
        email = form.email.data
        firstName = form.firstName.data
        lastName = form.lastName.data
        yearLevel = form.yearLevel.data
        tutorGroup = form.tutorGroup.data
        role = form.role.data
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "INSERT INTO userstable(userName, password, email, firstName, lastName, yearLevel, tutorGroup, role) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
            vals = (userName, password, email, firstName, lastName, yearLevel, tutorGroup, role)
            cursor.execute(sql, vals)
            connection.commit()
            connection.close()
        if request.method == "POST":
            msg = Message('Pakuranga College Art Resources - Registration complete', sender = 'pakcollegeartdepartment@gmail.com', recipients = [(email)])
            msg.body = "Hey there. You have just successfully registered an account for Pakuranga College Art Resources. If you don't recognise this account, feel free to disregard this email."
            mail.send(msg)
            return render_template("login.html")
        else:
            return render_template("login.html")
        return render_template("login.html")
    else:
        return render_template("register.html", form = form)

# Brings up profile page and fetches values
@app.route("/profile")
def profile():
    if session["loggedIn"] == True:
        form = registerForm(request.form)
        userID = int(request.args["userID"])
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM usersTable WHERE userID = %s;"
            vals = (userID)
            cursor.execute(sql, vals)
            this_user = cursor.fetchone()
            connection.close()
        return render_template("profile.html", this_user = this_user, form = form)
    else:
        return redirect('/')

# Perform the update profile with updated values from form
@app.route('/profileUpdate', methods = ["GET", "POST"])
def profileUpdate():
   form = registerForm(request.form)
   email = form.email.data
   firstName = form.firstName.data
   lastName = form.lastName.data
   userName = form.userName.data
   yearLevel = form.yearLevel.data
   tutorGroup = form.tutorGroup.data
   password = form.password.data
   password = md5(password.encode()).hexdigest()
   userID = request.form["userID"]
   connection = create_connection()
   with connection.cursor() as cursor:
       sql = "UPDATE userstable SET email = %s, firstName = %s, lastName = %s, userName = %s, yearLevel = %s, tutorGroup = %s, password = %s WHERE userID = %s"
       vals = (email, firstName, lastName, userName, yearLevel, tutorGroup, password, userID)
       cursor.execute(sql, vals)
       connection.commit()
       connection.close()
   return redirect('/borrow')

if __name__ == '__main__':
    import os
    app.secret_key = os.urandom(12)
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)