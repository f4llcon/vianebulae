from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm, ProfileForm, ReviewForm, BookForm, MovieForm, GameForm, ISBNForm, IMDBForm
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from urllib.parse import quote
from sqlalchemy.sql.expression import func
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'twystedspyne' # Change to an actually secure key if required
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' 
app.config['UPLOAD_FOLDER'] = 'static/images'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Data Models for the Database site.db
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)    
    password = db.Column(db.String(60), nullable=False)
    bio = db.Column(db.String(180), nullable=True)
    book_reviews = db.relationship('BookReview', backref='user', lazy=True)
    game_reviews = db.relationship('GameReview', backref='user', lazy=True)
    movie_reviews = db.relationship('MovieReview', backref='user', lazy=True)
    avatar = db.Column(db.String(255), default='default_avatar.png') 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(255), nullable=False)
    synopsis = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), default='default_cover.png')
    reviews = db.relationship('BookReview', backref='book', lazy=True)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    studio = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(255), nullable=False)
    synopsis = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), default='default_cover.png')
    reviews = db.relationship('GameReview', backref='game', lazy=True)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    director = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(255), nullable=False)
    synopsis = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), default='default_cover.png')
    reviews = db.relationship('MovieReview', backref='movie', lazy=True)

class BookReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

class MovieReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

class GameReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)

# Routes
@app.route('/')
def index():
    # show 5 random things from the database
    random_books = Book.query.order_by(func.random()).limit(5).all()   
    random_movies = Movie.query.order_by(func.random()).limit(5).all()  
    random_games = Game.query.order_by(func.random()).limit(5).all()  

    return render_template('index.html', random_books=random_books, random_movies=random_movies, random_games=random_games)

@app.route('/books')
def books():
    all_books = Book.query.order_by(func.random()).all()  

    return render_template('books.html', all_books=all_books)

@app.route('/movies')
def movies():
    all_movies = Movie.query.order_by(func.random()).all()  

    return render_template('movies.html', all_movies=all_movies)

@app.route('/games')
def games():
    all_games = Game.query.order_by(func.random()).all()  

    return render_template('games.html', all_games=all_games)

@app.route('/book/<int:book_id>')
def book(book_id):
    form = ReviewForm()
    book = Book.query.get_or_404(book_id)
    reviews = BookReview.query.filter_by(book_id=book_id).all()
    return render_template('book.html', book=book, reviews=reviews, form=form)

@app.route('/movie/<int:movie_id>')
def movie(movie_id):
    form = ReviewForm()
    movie = Movie.query.get_or_404(movie_id)
    reviews = MovieReview.query.filter_by(movie_id=movie_id).all()
    return render_template('movie.html', movie=movie, reviews=reviews, form=form)

@app.route('/game/<int:game_id>')
def game(game_id):
    form = ReviewForm()
    game = Game.query.get_or_404(game_id)
    reviews = GameReview.query.filter_by(game_id=game_id).all()
    return render_template('game.html', game=game, reviews=reviews, form=form)

@app.route('/add_review/<item_type>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def add_review(item_type, item_id):
    item_model = None
    review_model = None
    form = ReviewForm()

    # figure out the correct models
    if item_type == 'book':
        item_model = Book
        review_model = BookReview
    elif item_type == 'movie':
        item_model = Movie
        review_model = MovieReview
    elif item_type == 'game':
        item_model = Game
        review_model = GameReview
    else:
        flash('Invalid item type.', 'danger')
        return render_template(url_for('index'))

    item = item_model.query.get_or_404(item_id)

    if form.validate_on_submit():
        content = form.review_content.data
        new_review = review_model(content=content, user_id=current_user.id, **{f"{item_type}_id": item_id})
        db.session.add(new_review)
        db.session.commit()
        
        # redirect user back to where they came from
        if review_model == BookReview:
            return redirect(url_for('book', book_id=item_id))
        elif review_model == MovieReview:
            return redirect(url_for('movie', movie_id=item_id))
        elif review_model == GameReview:
            return redirect(url_for('game', game_id=item_id))

    return redirect(url_for(item_type, item_id=item_id))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    return render_template('add.html')

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    isbn_form = ISBNForm()
    form = BookForm()
    # If ISBN is provided, fetch book details from Open Library API
    if isbn_form.validate_on_submit():
        flash('ISBN form submitted', 'info')
        isbn = isbn_form.isbn.data
        api_url = f'https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json'
        response = requests.get(api_url)

        if response.status_code == 200:
            book_data = response.json().get(f'ISBN:{isbn}')
        
            if book_data:
                # Extract book details from the Open Library API response
                form.title.data = book_data.get('title', '')
                authors = [author.get('name', '') for author in book_data.get('authors', [])]
                form.author.data = ', '.join(authors)
                # Extract subject and excerpts from the list of dictionaries
                genres = [subject.get('name', '') for subject in book_data.get('subjects', [])[:3]]
                form.genre.data = ', '.join(genres)
                synopses = [excerpt.get('text', '') for excerpt in book_data.get('excerpts', [])]
                form.synopsis.data = ', '.join(synopses)
                # Extract cover image
                cover_url = book_data.get('cover', {}).get('medium')
                if cover_url: # If cover image is available
                    flash(f'Book details fetched successfully. ISBN: {isbn}', 'success')
                    response = requests.get(cover_url)
                    if response.status_code == 200: # If the link can be accessed
                        flash('Book cover submitted', 'info')
                        cover_image_filename = f'{secure_filename(form.title.data.replace(" ", "_"))}_cover.jpg'
                        invalid_chars = r'<>:"/\|?*'
                        for char in invalid_chars: # make sure the filename does not consist of illegal chars
                            cover_image_filename = cover_image_filename.replace(char, "")
                        cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_filename)
                        with open(cover_image_path, 'wb') as img_file:
                            img_file.write(response.content) # write the image to the server on the path
                    return render_template('add_book.html', isbn_form=isbn_form, form=form, cover_url=cover_url)
                else:
                    flash(f'Book details fetched successfully. ISBN: {isbn} (No thumbnail available)', 'success')
                    return render_template('add_book.html', isbn_form=isbn_form, form=form)
            else:
                flash(f'No book details found for ISBN: {isbn}. Please enter the details manually.', 'warning')
        else:
            flash('Error fetching book details. Please try again.', 'danger')

    if form.validate_on_submit():
        flash('Book details form submitted', 'info')
        cover_image_filename = None

        if form.cover_image.data:
            # Cover image uploaded by the user
            cover_image = form.cover_image.data
            cover_image_filename = secure_filename(cover_image.filename)
            cover_image_filename = f'{form.title.data.replace(" ", "_")}_cover.jpg'
            invalid_chars = r'<>:"/\|?*'
            for char in invalid_chars:
                cover_image_filename = cover_image_filename.replace(char, "")
            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_filename)
            cover_image.save(cover_image_path)

        else: # Cover image not uploaded, check if downloaded from Open Library or otherwise
            cover_image_filename = f'{form.title.data.replace(" ", "_")}_cover.jpg'
            invalid_chars = r'<>:"/\|?*'
            for char in invalid_chars:
                cover_image_filename = cover_image_filename.replace(char, "")
            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_filename)
            if os.path.exists(cover_image_path):
                pass
            else: 
                flash('Cover image unavailable. Please upload.', 'danger') # There is a default cover image, so this can be removed
                return redirect(url_for('add_book'))            

        # Create a new book
        new_book = Book(
            title=form.title.data,
            author=form.author.data,
            genre=form.genre.data,
            synopsis=form.synopsis.data,
            cover_image=cover_image_filename
        )

        # Add the new book to the database
        db.session.add(new_book)
        db.session.commit()

        flash('Book added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_book.html', form=form, isbn_form=isbn_form)

@app.route('/add_movie', methods=['GET', 'POST'])
@login_required
def add_movie():
    imdb_form = IMDBForm()
    form = MovieForm()
    # If IMDB is provided, fetch book details from Open Movie DB
    if imdb_form.validate_on_submit():
        flash('IMDB form submitted', 'info')
        imdb = imdb_form.imdb.data
        api_url = f'http://www.omdbapi.com/?i={imdb}&apikey=8d437aa0'
        response = requests.get(api_url)

        if response.status_code == 200:
            movie_data = response.json()

            if movie_data.get('Response') == 'True':
                # Extract movie details from the OMDB API response
                form.title.data = movie_data.get('Title', '')
                form.director.data = movie_data.get('Director', '')
                form.genre.data = movie_data.get('Genre', '')
                form.synopsis.data = movie_data.get('Plot', '')
                form.cover_image.data = movie_data.get('Poster', '')
                # The code below is virtually identical to the add_book route
                if form.cover_image.data:
                    response_cover = requests.get(form.cover_image.data)
                    if response_cover.status_code == 200:
                        cover_image_filename = f'{secure_filename(form.title.data.replace(" ", "_"))}_cover.jpg'
                        invalid_chars = r'<>:"/\|?*'
                        for char in invalid_chars:
                            cover_image_filename = cover_image_filename.replace(char, "")
                        cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_filename)
                        with open(cover_image_path, 'wb') as img_file:
                            img_file.write(response_cover.content)
                        flash('Movie details and cover fetched successfully.', 'success')
                        return render_template('add_movie.html', imdb_form=imdb_form, form=form)
                    else:
                        flash('Error downloading movie cover. Please try again.', 'danger')
                else:
                    flash('Movie details fetched successfully. No cover found.', 'success')
                    return render_template('add_movie.html', imdb_form=imdb_form, form=form)
            else:
                flash(f'Error: {movie_data.get("Error")}', 'danger')
        else:
            flash('Error fetching movie details. Please try again.', 'danger')

    if form.validate_on_submit():
        # This is identical to the add_book route
        flash('Movie details form submitted', 'info')
        cover_image_filename = None

        if form.cover_image.data:
            # Cover image uploaded by the user
            cover_image = form.cover_image.data
            cover_image_filename = secure_filename(cover_image.filename)
            cover_image_filename = f'{form.title.data.replace(" ", "_")}_cover.jpg'
            invalid_chars = r'<>:"/\|?*'
            for char in invalid_chars:
                cover_image_filename = cover_image_filename.replace(char, "")
            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_filename)
            cover_image.save(cover_image_path)

        else:
            cover_image_filename = f'{form.title.data.replace(" ", "_")}_cover.jpg'
            invalid_chars = r'<>:"/\|?*'
            for char in invalid_chars:
                cover_image_filename = cover_image_filename.replace(char, "")
            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_filename)

            if os.path.exists(cover_image_path):
                pass
            else: 
                flash('Cover image unavailable. Please upload.', 'danger')
                return redirect(url_for('add_movie'))            

        # Create a new movie
        new_movie = Movie(
            title=form.title.data,
            director=form.director.data,
            genre=form.genre.data,
            synopsis=form.synopsis.data,
            cover_image=cover_image_filename
        )

        # Add the new movie to the database
        db.session.add(new_movie)
        db.session.commit()

        flash('Movie added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_movie.html', form=form, imdb_form=imdb_form)

@app.route('/add_game', methods=['GET', 'POST'])
@login_required
def add_game():
    form = GameForm()
    # There is no API configured for this route, and it is identical to add_movie or add_book route's form validation function
    if form.validate_on_submit():
        flash('Game details form submitted', 'info')
        cover_image_filename = None

        if form.cover_image.data:
            # Cover image uploaded by the user
            cover_image = form.cover_image.data
            cover_image_filename = secure_filename(cover_image.filename)
            cover_image_filename = f'{form.title.data.replace(" ", "_")}_cover.jpg'
            invalid_chars = r'<>:"/\|?*'
            for char in invalid_chars:
                cover_image_filename = cover_image_filename.replace(char, "")
            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_filename)
            cover_image.save(cover_image_path)

        else:
            cover_image_filename = f'{form.title.data.replace(" ", "_")}_cover.jpg'
            invalid_chars = r'<>:"/\|?*'
            for char in invalid_chars:
                cover_image_filename = cover_image_filename.replace(char, "")
            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_filename)

            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_image_path)
            if os.path.exists(cover_image_path):
                pass
            else: 
                flash('Cover image unavailable. Please upload.', 'danger')
                return redirect(url_for('add_game'))            

        # Create a new game
        new_game = Game(
            title=form.title.data,
            studio=form.studio.data,
            genre=form.genre.data,
            synopsis=form.synopsis.data,
            cover_image=cover_image_filename
        )

        # Add the new game to the database
        db.session.add(new_game)
        db.session.commit()

        flash('Game added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_game.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST':
        # Check if the user exists
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            # Log in the user
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
            return redirect(url_for('index'))

    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    # Log out the user
    logout_user()
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # Check if the username or email is already taken
        existing_user = User.query.filter(
            (User.username == form.username.data)
        ).first()

        if existing_user:
            flash('Username already taken. Please choose another.', 'danger')
            return redirect(url_for('index'))

        # Create a new user
        hashed_password = generate_password_hash(form.password.data, method="pbkdf2", salt_length=16)
        user = User(username=form.username.data, password=hashed_password)

        # Add the new user to the database
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/user_profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    # This route is for the configure profile route only visible to the user themselves
    form = ProfileForm()

    if form.validate_on_submit():
        # Save avatar
        if form.avatar.data:
            avatar = form.avatar.data
            avatar_filename = secure_filename(avatar.filename)
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', avatar_filename)
            avatar.save(avatar_path)
            current_user.avatar = avatar_filename

        # Update user bio
        current_user.bio = form.bio.data

        # Save changes to the database
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile'))

    form.bio.data = current_user.bio
    all_reviews = current_user.book_reviews + current_user.game_reviews + current_user.movie_reviews
    reviews = sorted(all_reviews, key=lambda review: review.id, reverse=True) # This sorts the user's reviews by ID

    return render_template('user_profile.html', form=form, reviews=reviews)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    # This route is for the public profile
    user = User.query.get_or_404(user_id)
    
    # Combine all reviews and order them by timestamp
    all_reviews = user.book_reviews + user.game_reviews + user.movie_reviews
    reviews = sorted(all_reviews, key=lambda review: review.id, reverse=True)
    
    return render_template('profile.html', user=user, reviews=reviews)

@app.route('/delete_review/<string:item_type>/<int:item_id>/<int:review_id>', methods=['POST'])
@login_required
def delete_review(item_type, item_id, review_id):
    review_model = None

    # Determine the review model based on the item_type
    if item_type == 'book':
        review_model = BookReview
    elif item_type == 'movie':
        review_model = MovieReview
    elif item_type == 'game':
        review_model = GameReview
    else:
        flash('Invalid item type.', 'danger')
        return redirect(url_for('index'))

    review = review_model.query.get_or_404(review_id)

    # Check if the current user is the author of the review
    if review.user_id == current_user.id or current_user.id == 1:
        db.session.delete(review)
        db.session.commit()
        flash('Review deleted successfully!', 'success')

    # Redirect back to the item page
    if review_model == BookReview:
        return redirect(url_for('book', book_id=item_id))
    elif review_model == MovieReview:
        return redirect(url_for('movie', movie_id=item_id))
    elif review_model == GameReview:
        return redirect(url_for('game', game_id=item_id))

@app.route('/delete_entry/<string:item_type>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def delete_entry(item_type, item_id):
    # This route allows for the deletion of books / movies / games by an administrator, checked using user id
    model = None

    # Determine the model based on the item_type
    if item_type == 'book':
        model = Book
    elif item_type == 'movie':
        model = Movie
    elif item_type == 'game':
        model = Game
    else:
        flash('Invalid item type.', 'danger')
        return redirect(url_for('index'))

    entry = model.query.get_or_404(item_id)

    # Check if the current user is administrator
    if current_user.id == 1:
        db.session.delete(entry)
        db.session.commit()
        flash('Entry deleted successfully!', 'success')

    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('lost.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
