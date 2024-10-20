from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class ProfileForm(FlaskForm):
    avatar = FileField('Avatar (Square Image)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    submit = SubmitField('Update Profile')

class ReviewForm(FlaskForm):
    review_content = TextAreaField('Write your review', validators=[DataRequired(), Length(min=10)])
    submit_review = SubmitField('Submit Review')

class BookForm(FlaskForm):
    title = StringField('Book Title', validators=[DataRequired(), Length(min=1, max=100)])
    author = StringField('Book Author', validators=[DataRequired(), Length(min=1, max=50)])
    genre = StringField('Book Genre', validators=[DataRequired(), Length(min=1)])
    cover_image = FileField('Cover Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    synopsis = TextAreaField('Book Description')
    submit_book = SubmitField('Submit Book')

class MovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired(), Length(min=1, max=100)])
    director = StringField('Movie Director', validators=[DataRequired(), Length(min=1, max=50)])
    genre = StringField('Movie Genre', validators=[DataRequired(), Length(min=1, max=50)])
    synopsis = TextAreaField('Movie Description', validators=[DataRequired(), Length(min=10)])
    cover_image = FileField('Cover Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit_movie = SubmitField('Submit Movie')

class GameForm(FlaskForm):
    title = StringField('Game Title', validators=[DataRequired(), Length(min=1, max=100)])
    studio = StringField('Game Studio', validators=[DataRequired(), Length(min=1, max=50)])
    genre = StringField('Game Genre', validators=[DataRequired(), Length(min=1, max=50)])
    synopsis = TextAreaField('Game Description', validators=[DataRequired(), Length(min=10)])
    cover_image = FileField('Cover Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit_game = SubmitField('Submit Game')

class ISBNForm(FlaskForm):
    isbn = StringField('ISBN', validators=[DataRequired()])
    submit_isbn = SubmitField('Submit ISBN')

class IMDBForm(FlaskForm):
    imdb = StringField('IMDB ID', validators=[DataRequired()])
    submit_isbn = SubmitField('Submit IMDB ID')