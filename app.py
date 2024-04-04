import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from models import User,  Article, Favorite, Comment, Likes, db, connect_db
from forms import LoginForm, UserAddForm
from flask_bcrypt import Bcrypt
from config import API_KEY

app = Flask(__name__)
bcrypt = Bcrypt(app)
# Set up the secret key and database URI
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://krndjncc:a5gxr03jVlcmiGbkRlXfW56vA1k3IZn8@raja.db.elephantsql.com/krndjncc'
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
    print("Fetching articles for homepage")  
    response = requests.get('https://newsapi.org/v2/top-headlines', params={'country': 'us', 'apiKey': API_KEY})

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
       

        # Check if the username or email already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Username already exists. Please choose a different one.", 'danger')
            return redirect(url_for('signup'))
        
        if existing_email:
            flash("Email already exists. Please use a different one.", 'danger')
            return redirect(url_for('signup'))

        new_user = User(username=username, email=email)
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
        comment.liked_by_user = like is not None  

    return render_template('comments.html', article=article, comments=comments)

@app.route('/like_comment/<int:comment_id>', methods=['POST'])
@login_required
def like_comment(comment_id):
        # Retrieve the comment from the database
        comment = Comment.query.get_or_404(comment_id)

        # Check if the current user has already liked the comment
        like = Likes.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

        if like:
            # If the user has already liked the comment, unlike it
            db.session.delete(like)
        else:
            # If the user has not liked the comment, like it
            new_like = Likes(user_id=current_user.id, comment_id=comment_id)
            db.session.add(new_like)

        # Commit the changes to the database
        db.session.commit()

        # Return a success response
        return jsonify({'success': True})


@app.route('/create_article', methods=['POST'])
def create_article():
    # Get the article URL and title (assuming they're submitted via a form)
    article_url = request.form.get('article_url')
    article_title = request.form.get('article_title')

    

    
    article = Article.query.filter_by(url=article_url).first()  

    if article is None:
       
        article = Article(url=article_url, title=article_title)  
        db.session.add(article)
        db.session.commit() 

    # Redirect the user to the article's page (or any other page as needed)
    return redirect(url_for('article_comments', article_id=article.id))




@app.route('/like_comment_toggle/<int:comment_id>', methods=['POST'])
@login_required
def like_comment_toggle(comment_id):
    # Get the comment from the database
    comment = Comment.query.get_or_404(comment_id)

    # Check if the user has already liked the comment
    existing_like = Likes.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

    if existing_like:
        # If the user has already liked the comment, remove their like
        db.session.delete(existing_like)
        # Decrement the likes count in the comments table
        comment.likes_count -= 1
        is_liked = False
    else:
        # If the user has not liked the comment, add their like
        new_like = Likes(user_id=current_user.id, comment_id=comment_id)
        db.session.add(new_like)
        # Increment the likes count in the comments table
        comment.likes_count += 1
        is_liked = True

    # Commit the changes to the database
    db.session.commit()

    # Return the updated likes count and the current liked status
    return jsonify({'likes_count': comment.likes_count, 'is_liked': is_liked})





  

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
