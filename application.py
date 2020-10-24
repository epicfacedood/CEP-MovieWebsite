import os
from flask import flash
from flask import Flask, session, render_template, request, redirect, url_for, logging, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
import requests


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def number(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


@app.route("/")
def default():
    return render_template("home.html")
@app.route("/home")
def home():
    return render_template("home.html")

class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    users = db.execute("SELECT * FROM users")
    form = RegisterForm(request.form)
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data
        uncheck = db.execute("SELECT * FROM users WHERE username = :un", {"un":username}).fetchone()
        pwcheck = db.execute("SELECT * FROM users WHERE password = :pw", {"pw":password}).fetchone()
        if pwcheck == None and uncheck == None:
            db.execute("INSERT into users(username,password) VALUES (:un,:pw)",{"un":username,"pw":password})
            db.commit()
            flash('Your Registration is a Success')
            return redirect(url_for("home"))
        else:
            error = "Already Exists!"
            return render_template('register.html', error=error,form=form)


        
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        uncheck = db.execute("SELECT * FROM users WHERE username = :un", {"un":username}).fetchone()
        pwcheck = db.execute("SELECT * FROM users WHERE password = :pw", {"pw":password_candidate}).fetchone()
        if uncheck == None:
            error = 'No such username'
            return render_template('login.html', error=error)
        elif pwcheck == None:
            error = 'Invalid Login'
            return render_template('login.html', error=error)
        else:
            session['logged_in'] = True
            session['username'] = username
            flash("You are successfully logged in," + session["username"] + '!')
            return redirect(url_for('home'))
            
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if session['logged_in'] == True:
        session.clear()
    return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        search = request.form['search'].replace(" ","").lower()
        if number(search) == True:
            ycheck = db.execute("SELECT * FROM movies WHERE year LIKE :year", {"year":"%"+search+"%"}).fetchall()
        else:
            ycheck = []
        print(ycheck)
        mcheck = db.execute("SELECT * FROM movies WHERE lowercase_title LIKE :title", {"title":"%"+search+"%"}).fetchall()
        idcheck = db.execute("SELECT * FROM movies WHERE imdbID LIKE :id", {"id":"%"+search+"%"}).fetchall()
        return render_template("movies.html",results=mcheck,results2=ycheck,results3=idcheck)
    return render_template("search.html")

class RatingForm(Form):
    review = StringField('review', [validators.Length(min=1, max=1000)])
    rating = StringField('rating', [validators.Length(min=1, max=4)])


@app.route("/movies/<imdbid>", methods=['GET', 'POST'])
def movies(imdbid):
    username = session["username"]
    movie = db.execute("SELECT * FROM movies WHERE imdbid = :id", {"id": imdbid}).fetchone()
    reviews = db.execute("SELECT * FROM reviews where imdbid = :id", {"id":imdbid}).fetchall()
    form = RatingForm(request.form)
    
        
    if request.method == "POST":
        username = session["username"]
        rating = form.rating.data
        review = form.review.data
        if number(rating) == False:
            error = ("Numbers, Please!")
            return render_template('movie.html', movie=movie,reviews=reviews,error=error)
        elif number(rating) == True and 4 > len(str(rating)):
            db.execute("INSERT into reviews(rating,review,imdbid,username) VALUES (:ra,:rv,:id,:un)",{"ra":rating,"rv":review,"id":imdbid,"un":username})
            db.commit()
            flash("Thank You for your Review, your review will be here the next time you visit this movie site!")
            return render_template('movie.html', movie=movie,reviews=reviews)
        else:
            error = ("Stop Trolling")
            return render_template('movie.html', movie=movie,reviews=reviews,error=error)
    else:
        return render_template('movie.html', movie=movie,reviews=reviews)


    return render_template("movie.html", movie=movie,reviews=reviews)
    


@app.route("/api/<imdbid>",methods=["GET"])
def api(imdbid):
    reviews = db.execute("SELECT * FROM reviews where imdbid = :id", {"id":imdbid}).fetchall()
    movie = db.execute("SELECT * FROM movies where imdbid =:id",{"id":imdbid}).fetchone()
    res = requests.get("http://www.omdbapi.com/", params={"apikey": "c7260cee", "t": str(movie.title.replace(" ","+"))})
    total = 0
    data = res.json()
    if len(reviews) != 0:
        for user in reviews:
            total += user.rating
    if total != 0:
        display = {"title":movie.title,"year":str(movie.year),"imdbid":movie.imdbid,"director":data["Director"]
        ,"imdbrating":str(movie.imdbrating),"reviewcount":str(len(reviews)),"averagerating":str(total/len(reviews)),"actors":data["Actors"]}
    else:
        display = {"title":movie.title,"year":str(movie.year),"imdbid":movie.imdbid,"director":data["Director"]
        ,"imdbrating":str(movie.imdbrating),"reviewcount":str(len(reviews)),"averagerating":"NO RATINGS YET","actors":data["Actors"]}
    return jsonify(display)





