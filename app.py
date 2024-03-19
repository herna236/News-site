import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, session, g, url_for, jsonify
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from models import User,  Article, Favorite, Comment, Likes, db, connect_db
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
           
            article['id'] = article['url']
            article['is_favorited'] = False  
            if current_user.is_authenticated:
                favorite = db.session.query(Favorite).join(Article).filter(Favorite.user_id == current_user.id, Article.url == article['url']).first()
                if favorite:
                    article['is_favorited'] = True
                print(f"Article: {article['title']}, Is Favorited: {article['is_favorited']}")

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

@app.route('/check_and_add_to_favorites', methods=['POST'])
@login_required
def check_and_add_to_favorites():
    article_title = request.form.get('article_title')
    article_url = request.form.get('article_url')

    article = Article.query.filter_by(url=article_url).first()

    if article is None:
        # If the article doesn't exist, create it in the database
        article = Article(title=article_title, url=article_url)
        db.session.add(article)
        db.session.commit()

    # Add the article to favorites for the current user
    favorite = Favorite(user_id=current_user.id, article_id=article.id, is_favorited=True)
    db.session.add(favorite)
    db.session.commit()

    return jsonify({'success': True})

@app.route('/article/<int:article_id>/comments', methods=['GET', 'POST'])
@login_required
def article_comments(article_id):
    article = Article.query.get(article_id)

    if not article:
        flash('Article not found.', 'danger')
        return redirect(url_for('homepage'))  # Redirect to a suitable route or render an error template

    if request.method == 'POST':
        # Handle comment submission
        comment_text = request.form.get('comment_text')
        
        if not comment_text:
            flash('Comment text is required.', 'danger')
            return redirect(url_for('article_comments', article_id=article_id))
        
        # Create a new comment instance
        new_comment = Comment(text=comment_text, article_id=article_id, user_id=current_user.id)
        
        # Add the new comment to the database
        db.session.add(new_comment)
        db.session.commit()

    comments = Comment.query.filter_by(article_id=article.id).all()

    # Adjust timestamp format and retrieve user name for each comment
    for comment in comments:
        comment.created_at = comment.timestamp.strftime('%m-%d-%Y %H:%M')
        user = User.query.get(comment.user_id)
        comment.user_name = user.username

        # Check if the current user has liked this comment
        like = Likes.query.filter_by(user_id=current_user.id, comment_id=comment.id).first()
        comment.liked_by_user = like is not None  # Set liked_by_user attribute

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



@app.route('/like_comment/<int:comment_id>', methods=['POST'])
@login_required
def like_comment(comment_id):
    # Get the comment ID from the URL
    comment_id = int(comment_id)  # Ensure comment_id is an integer

    # Check if the user has already liked the comment
    like = Likes.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

    if like:
        # If the user has already liked the comment, update is_liked to True
        like.is_liked = True
    else:
        # If the user has not liked the comment, create a new like with is_liked set to True
        new_like = Likes(user_id=current_user.id, comment_id=comment_id, is_liked=True)
        db.session.add(new_like)

    # Update the likes count in the comments table
    comment = Comment.query.get(comment_id)
    comment.likes_count += 1
    db.session.commit()

    # Return the updated likes count
    return jsonify({'likes_count': comment.likes_count})


  

@app.route('/user/<int:user_id>/favorites')
def user_favorites(user_id):
    # Query the database to retrieve the user's favorited articles
    user_favorites = (Favorite.query
                      .join(User)
                      .filter(User.id == user_id)
                      .all())

    # Extract the articles from the favorites
    articles = [fav.article for fav in user_favorites]
    user = User.query.get(user_id)
    # Render a template to display the user's favorited articles
    return render_template('user_favorites.html', user=user, articles=articles)

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
