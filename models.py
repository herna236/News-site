import os
from datetime import datetime
from flask import url_for
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash



bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """Connect this database to provided Flask app."""
    db.app = app
    db.init_app(app)


class Favorite(db.Model):
    """Connection of a user <-> favorited_article."""

    __tablename__ = 'user_favorite'

    article_being_favorited_id = db.Column(
        db.Integer,
        db.ForeignKey('articles.id', ondelete="cascade"),
        primary_key=True,
    )

    user_favorited_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )


class Likes(db.Model):
    """Mapping user to liked articles."""

    __tablename__ = 'likes'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    article_id = db.Column(
        db.Integer,
        db.ForeignKey('articles.id', ondelete='cascade')
    )



class User(UserMixin, db.Model):
    """User model."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    img_url = db.Column(db.String(500), nullable=True, default='default_image_url.jpg')
    is_active = db.Column(db.Boolean(), default=True)
    
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    

class Article(db.Model):
    """Article fetched from an API."""

    __tablename__ = 'articles'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    url = db.Column(
        db.String,
        unique=True,
        nullable=False,
    )

    title = db.Column(
        db.Text,
        nullable=False,
    )


class Comment(db.Model):
    """An individual comment."""

    __tablename__ = 'comments'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    text = db.Column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    article_id = db.Column(
        db.Integer,
        db.ForeignKey('articles.id', ondelete='CASCADE'),
        nullable=False
    )

    author = db.relationship('User', backref=db.backref('comments', lazy=True))


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
