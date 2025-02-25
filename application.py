import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    isbn = db.Column(db.String(50), unique=True, nullable=False)

class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    user = db.relationship("User", backref="reviews")
    book = db.relationship("Book", backref="reviews")

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("search"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except IntegrityError:
            db.session.rollback()
            flash("Username already taken. Please choose another.", "danger")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login successful.", "success")
            return redirect(url_for("search"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("login"))

@app.route("/search", methods=["GET", "POST"])
def search():
    if "user_id" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    books = []
    if request.method == "POST":
        query = request.form.get("query").strip()
        
        if query.isdigit():
            books = Book.query.filter_by(year=int(query)).all()
        else:
            books = Book.query.filter(
                (Book.title.ilike(f"%{query}%")) |
                (Book.author.ilike(f"%{query}%")) |
                (Book.isbn.ilike(f"%{query}%"))
            ).all()

    return render_template("search.html", books=books)

@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book_details(book_id):
    if "user_id" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    book = Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book_id).all()

    existing_review = Review.query.filter_by(book_id=book_id, user_id=session["user_id"]).first()
    if request.method == "POST":
        if existing_review:
            flash("You have already submitted a review for this book.", "danger")
        else:
            rating = int(request.form.get("rating"))
            comment = request.form.get("comment")
            new_review = Review(book_id=book_id, user_id=session["user_id"], rating=rating, comment=comment)
            db.session.add(new_review)
            db.session.commit()
            flash("Review submitted.", "success")
            return redirect(url_for("book_details", book_id=book_id))

    return render_template("book_details.html", book=book, reviews=reviews, existing_review=existing_review)

@app.route("/api/book/<int:book_id>/reviews")
def api_reviews(book_id):
    reviews = Review.query.filter_by(book_id=book_id).all()
    if not reviews:
        return jsonify({"error": "No reviews found"}), 404
    
    return jsonify([
        {"username": review.user.username, "rating": review.rating, "comment": review.comment}
        for review in reviews
    ])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
