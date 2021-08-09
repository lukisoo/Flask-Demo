"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""
import os
import uuid
from flask import Flask, render_template, request, redirect, abort, flash
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SelectField
from wtforms.validators import NumberRange, DataRequired, Length
from datetime import datetime
import pymysql
from hashlib import md5

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisisasecret!'

from users import *
from utils import *

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

# Form with the different fields included within the resources database, and the validation for each field.
class resourceForm(FlaskForm):
   resourceType = SelectField('Resource Type:', choices=[('Camera', 'Camera'),('Lens', 'Lens'),('Tripod Stand', 'Tripod Stand'),('Other', 'Other')])
   resourceBrand = StringField('Brand:', validators = [Length(max=30, message="Your input must be between 0 and 30 characters long.")])
   resourceModel = StringField('Model:', validators = [Length(max=30, message="Your input must be between 0 and 30 characters long.")])
   purchaseDate = DateField('Purchase Date:', format="%Y-%m-%d", default = datetime.today, validators = [DataRequired(message="The purchase date must be entered in the format 'xxxx-xx-xx', where 'year-month-day'.")])
   purchasePrice = IntegerField('Purchase Price:', default = 0, validators = [NumberRange(min=0, max=99999, message="Must not exceed 5 digits, and cannot be a negative number.")])
   resourceCondition = StringField('Resource Condition:', validators = [Length(max=60, message="Your input must be between 0 and 60 characters long.")])
   lensAttached = StringField('Lens Attached:', validators = [Length(max=60, message="Your input must be between 0 and 60 characters long.")])
   extraNotes = StringField('Extra Notes:', validators = [Length(max=60, message="Your input must be between 0 and 60 characters long.")])

#Creates connection to the SQL database
def create_connection():
  return pymysql.connect(
       host = '127.0.0.1',
       user = 'root',
       password = 'pasword1089',
       db = 'resourcesdatabase',
       charset = 'utf8mb4',
       cursorclass = pymysql.cursors.DictCursor
       )

# Default index page the site opens to
@app.route('/')
def homepage():
    if session.get("loggedIn"):
        if session["loggedIn"]:
            print("User is logged in.")
    return render_template("homepage.html")

@app.route('/gallery')
def gallery():
    return render_template("gallery.html")

# Selects, reads, and displays the information on the database
@app.route('/viewdatabase')
def viewdatabase():
   connection = create_connection()
   with connection.cursor() as cursor:
       sql = "SELECT resourceID, resourceImage, resourceType, resourceBrand, resourceModel, purchaseDate, purchasePrice, resourceCondition, lensAttached, extraNotes FROM resourcestable;"
       cursor.execute(sql)
       resources = cursor.fetchall()
       connection.close()
   return render_template("viewdatabase.html", resources = resources)

# Database display with added controls depending on user permissions
@app.route('/database')
def database():
    if session["role"] == "Teacher" or session["role"] == "Admin":
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT resourceID, resourceImage, resourceType, resourceBrand, resourceModel, purchaseDate, purchasePrice, resourceCondition, lensAttached, extraNotes FROM resourcestable;"
            cursor.execute(sql)
            resources = cursor.fetchall()
            connection.close()
        return render_template("database.html", resources = resources)
    else:
        return redirect ('/')

#  Creating a new data entry for the database
@app.route('/create', methods=['GET', 'POST'])
def create():
    if session["role"] == "Teacher" or session["role"] == "Admin":
        form = resourceForm(request.form)
        if request.method == 'POST' and form.validate():
            resourceImage = request.files["resourceImage"]
            if resourceImage.filename == '':
                # If the user has not uploaded an image, the image displayed for the entry will be a default blank image
                resourceImageName = "blank.png"
            else:
                # If the user has uploaded an image, it will add this image into static/images, and display the uploaded image under a unique name
                resourceImageName = str(uuid.uuid1()) + os.path.splitext(resourceImage.filename)[1]
                resourceImage.save(os.path.join("static/images", resourceImageName))
            resourceType = form.resourceType.data
            resourceBrand = form.resourceBrand.data
            resourceModel = form.resourceModel.data
            purchaseDate = form.purchaseDate.data
            purchasePrice = form.purchasePrice.data
            lensAttached = form.lensAttached.data
            resourceCondition = form.resourceCondition.data
            extraNotes = form.extraNotes.data
            connection = create_connection()
            with connection.cursor() as cursor:
                sql = "INSERT INTO resourcesTable (resourceImage, resourceType, resourceBrand, resourceModel, purchaseDate, purchasePrice, resourceCondition, lensAttached, extraNotes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                vals = (resourceImageName, resourceType, resourceBrand, resourceModel, purchaseDate, purchasePrice, resourceCondition, lensAttached, extraNotes)
                cursor.execute(sql, vals)
                connection.commit()
                connection.close()
            return redirect("/database")
        else:
            return render_template('create.html', form = form)
    else:
        return redirect('/')

# Displaying and entering data for updating certain existing data entry within the database
@app.route('/update')
def update():
    if session["role"] == "Teacher" or session["role"] == "Admin":
        form = resourceForm(request.form)
        resourceID = int(request.args["resourceID"])
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM resourcesTable WHERE resourceID = %s;"
            vals = (resourceID)
            cursor.execute(sql, vals)
            this_resource = cursor.fetchone()
            connection.close()
        return render_template("update.html", this_resource = this_resource, form = form)
    else:
        return redirect('/')

# Perform the update with updated values from form
@app.route('/performUpdate', methods = ["GET", "POST"])
def performUpdate():
    form = resourceForm(request.form)
    resourceID = request.form["resourceID"]
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "SELECT * FROM resourcesTable WHERE resourceID = %s;"
        vals = (resourceID)
        cursor.execute(sql, vals)
        this_resource = cursor.fetchone()
        connection.close()
    if form.validate():
        resourceImage = request.files["resourceImage"]
        if resourceImage.filename == '':
            resourceImageName = "blank.png"
        else:
            resourceImageName = str(uuid.uuid1()) + os.path.splitext(resourceImage.filename)[1]
            resourceImage.save(os.path.join("static/images", resourceImageName))
        resourceType = form.resourceType.data
        resourceBrand = form.resourceBrand.data
        resourceModel = form.resourceModel.data
        purchaseDate = form.purchaseDate.data
        purchasePrice = form.purchasePrice.data
        lensAttached = form.lensAttached.data
        resourceCondition = form.resourceCondition.data
        extraNotes = form.extraNotes.data
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "UPDATE resourcesTable SET resourceImage = %s, resourceType = %s, resourceBrand= %s, resourceModel = %s, purchaseDate= %s, purchasePrice = %s, resourceCondition = %s, lensAttached = %s, extraNotes = %s WHERE resourceID = %s"
            vals = (resourceImageName, resourceType, resourceBrand, resourceModel, purchaseDate, purchasePrice, resourceCondition, lensAttached, extraNotes, resourceID)
            cursor.execute(sql, vals)
            connection.commit()
            connection.close()
        return redirect('/database')
    else:
        return render_template("update.html", this_resource = this_resource, form = form)

# Delete a certain entry off the database
@app.route('/deleteresource', methods = ["GET", "POST"])
def deleteresource():
   resourceID = int(request.args["resourceID"])
   connection = create_connection()
   with connection.cursor() as cursor:
       sql = "DELETE FROM resourcesTable WHERE resourceID = %s;"
       vals = (resourceID)
       cursor.execute(sql, vals)
       connection.commit()
       connection.close()
   return redirect('/database')

# Error displays if the user tries to access a page that doesn't exist
@app.errorhandler(404)
def page_not_found(e):
    flash("Sorry, that URL does not exist. You have been redirected back to the home page. Click here to close this message.", "alert alert-danger")
    return redirect("/")

# Error displays if the user tries to access a page that they do not have permission to access
@app.errorhandler(500)
def page_not_found(e):
    flash("Sorry, you do not have permission to access this page. Your account may not have sufficient permissions, or you have not logged in. You have been redirected back to the home page. Click here to close this message.", "alert alert-danger")
    return redirect("/")


if __name__ == '__main__':
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)