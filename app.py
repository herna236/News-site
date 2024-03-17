import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, session, g, url_for, jsonify
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from models import User,  Article, Favorite, Comment, db, connect_db
from forms import LoginForm, CommentForm, UserAddForm, UserEditForm
from flask_bcrypt import generate_password_hash, check_password_hash, Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
# Set up the secret key and database URI
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///hh')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
connect_db(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rest of your app...


# Rest of your app...


##############################################################################
# User signup/login/logout



@app.route('/')
def homepage():
    """Show homepage."""

    if current_user.is_authenticated:
        top_articles = get_articles_for_homepage()

        for article in top_articles:
            if 'publishedAt' in article:
                published_at = datetime.fromisoformat(article['publishedAt'][:-1])  # Remove 'Z'
                article['publishedAt'] = published_at.strftime('%m-%d-%Y')

        return render_template('home.html', top_articles=top_articles)
    else:
        print("Rendering home-anon.html")
        return render_template('home-anon.html')

def get_articles_for_homepage():
    print("Fetching articles for homepage")  # Debug print
    # Send a GET request to the API endpoint
    response = requests.get('https://newsapi.org/v2/top-headlines', params={'country': 'us', 'apiKey': 'e37703955bc344baac883221a3ea44a7'})

    if response.status_code == 200:
        # Parse the JSON response
        response_json = response.json()
        # Extract the list of articles
        articles = response_json.get('articles', [])
        # Extract the first 10 articles
        first_10_articles = articles[:10]

        return first_10_articles
    else:
        # If the request was unsuccessful, return an empty list
        return []

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Sign up user."""

    form = UserAddForm()  # Create an instance of the UserAddForm

    if form.validate_on_submit():
        # Process form data and sign up user
        username = form.username.data
        password = form.password.data
        email = form.email.data
        img_url = form.img_url.data

        # Check if the username or email already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Username already exists. Please choose a different one.", 'danger')
            return redirect(url_for('signup'))
        
        if existing_email:
            flash("Email already exists. Please use a different one.", 'danger')
            return redirect(url_for('signup'))

        new_user = User(username=username, email=email, img_url=img_url)
        new_user.set_password(password)

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # Log in the new user
        login_user(new_user)

        # Redirect to the homepage
        return redirect(url_for('homepage'))

    # If the request method is GET or form validation fails, render the signup form
    return render_template('/users/signup.html', form=form)



    



@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)  # Use login_user to log in the user
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")
        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)



@app.route('/logout', methods=['GET'])
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)

@app.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    # Get the article ID from the request data
    article_id = request.form.get('article_id')

    # Check if the article already exists in the database
    article = Article.query.filter_by(id=article_id).first()

    if article is None:
        # If the article doesn't exist, add it to the database
        article_name = request.form.get('article_name')  # Assuming you send article name in the request
        article_url = request.form.get('article_url')    # Assuming you send article URL in the request

        # Create a new article object and add it to the database
        article = Article(name=article_name, url=article_url)
        db.session.add(article)
        db.session.commit()

    # Get the current user's ID
    user_id = current_user.id

    # Check if the user has already favorited the article
    existing_favorite = Favorite.query.filter_by(user_id=user_id, article_id=article_id).first()

    if existing_favorite:
        # If the user has already favorited the article, return a response indicating it's already favorited
        return jsonify({'success': False, 'message': 'Article already favorited.'}), 400

    # If the article is not already favorited by the user, create a new Favorites object
    favorite = Favorite(user_id=user_id, article_id=article_id)

    # Add the favorite to the database
    db.session.add(favorite)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Article added to favorites.'})

from flask_login import current_user

@app.route('/article/<int:article_id>/comments', methods=['GET', 'POST'])
@login_required
def article_comments(article_id):
    if request.method == 'POST':
        comment_text = request.form.get('comment_text')

        # Fetch the article based on the provided ID
        article = Article.query.get(article_id)

        if not article:
            # If the article doesn't exist, redirect to create_article route
            return redirect(url_for('create_article'))

        # Create a new comment associated with the article
        new_comment = Comment(text=comment_text, article_id=article.id, user_id=current_user.id)
        db.session.add(new_comment)
        db.session.commit()

        # Redirect to the page that displays comments for the article
        return redirect(url_for('article_comments', article_id=article.id))

    # Fetch the article and its associated comments based on the ID
    article = Article.query.get(article_id)
    if not article:
        # If the article doesn't exist, redirect to create_article route
        return redirect(url_for('create_article'))

    comments = Comment.query.filter_by(article_id=article.id).all()

    # Adjust timestamp format and retrieve user name for each comment
    for comment in comments:
        comment.created_at = comment.timestamp.strftime('%m-%d-%Y %H:%M')
        user = User.query.get(comment.user_id)
        comment.user_name = user.username

    return render_template('comments.html', article=article, comments=comments)

@app.route('/create_article', methods=['POST'])
def create_article():
    # Get the article URL and title (assuming they're submitted via a form)
    article_url = request.form.get('article_url')
    article_title = request.form.get('article_title')

    # Corrected line: Filter by the 'url' attribute instead of 'link'
    article = Article.query.filter_by(url=article_url).first()  # Corrected line

    if article is None:
        # If the article doesn't exist, create a new instance with the provided URL and title
        article = Article(url=article_url, title=article_title)  # Updated attribute name
        db.session.add(article)
        db.session.commit()

    # Redirect the user to the article's page (or any other page as needed)
    return redirect(url_for('article_comments', article_id=article.id))

@app.route('/users/profile', methods=["GET", "POST"])
def edit_profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = g.user
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data or "/static/images/default-pic.png"
            user.header_image_url = form.header_image_url.data or "/static/images/warbler-hero.jpg"
            user.bio = form.bio.data

            db.session.commit()
            return redirect(f"/users/{user.id}")

        flash("Wrong password, please try again.", 'danger')

    return render_template('users/edit.html', form=form, user_id=user.id)

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

##############################################################################
# Error handling

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""
    return render_template('404.html'), 404

##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""
    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req

if __name__ == '__main__':
    app.run()
