from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, Length



class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    img_url = StringField('Image URL', default='')


class UserEditForm(FlaskForm):
    """Form for editing users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    image_url = StringField('(Optional) Image URL')
    header_image_url = StringField('(Optional) Header Image URL')
    bio = TextAreaField('(Optional) Tell us about yourself')
    password = PasswordField('Password', validators=[Length(min=6)])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class CommentForm(FlaskForm):
    """Form for adding comments."""

    text = TextAreaField('Text', validators=[DataRequired()])
    user_id = HiddenField('User ID', validators=[DataRequired()])