import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
DATABASE_URL = "postgresql://postgres:Sea22%40%40S@localhost/project1"
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))

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

        # Check if username exists
        existing_user = db.execute(text("SELECT id FROM users WHERE username = :username"),
                                   {"username": username}).fetchone()
        if existing_user:
            flash("Username already taken. Please choose another.", "danger")
            return redirect(url_for("register"))

        # Insert new user
        db.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"),
                   {"username": username, "password": password})
        db.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        # Check credentials
        user = db.execute(text("SELECT id, username FROM users WHERE username = :username AND password = :password"),
                          {"username": username, "password": password}).fetchone()
        if user:
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

# Book Search (Only Raw SQL)
@app.route("/search", methods=["GET", "POST"])
def search():
    if "user_id" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    books = []
    if request.method == "POST":
        query = request.form.get("query").strip()

        # Check if the query is a number (for year search)
        if query.isdigit():
            books = db.execute(text("SELECT * FROM books WHERE year = :query"), 
                               {"query": int(query)}).fetchall()
        else:
            books = db.execute(text("""
                SELECT * FROM books 
                WHERE LOWER(title) LIKE LOWER(:query) 
                   OR LOWER(author) LIKE LOWER(:query) 
                   OR isbn LIKE :query
            """), {"query": f"%{query}%"}).fetchall()

    return render_template("search.html", books=books)

# Book Details + Review Submission
@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book_details(book_id):
    if "user_id" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    book = db.execute(text("SELECT * FROM books WHERE id = :book_id"), {"book_id": book_id}).fetchone()
    reviews = db.execute(text("""
        SELECT r.rating, r.comment, u.username 
        FROM reviews r JOIN users u ON r.user_id = u.id 
        WHERE book_id = :book_id
    """), {"book_id": book_id}).fetchall()

    if request.method == "POST":
        rating = int(request.form.get("rating"))
        comment = request.form.get("comment")

        # Insert review
        db.execute(text("""
            INSERT INTO reviews (book_id, user_id, rating, comment) 
            VALUES (:book_id, :user_id, :rating, :comment)
        """), {"book_id": book_id, "user_id": session["user_id"], "rating": rating, "comment": comment})
        db.commit()

        flash("Review submitted.", "success")
        return redirect(url_for("book_details", book_id=book_id))

    return render_template("book_details.html", book=book, reviews=reviews)

# API Endpoint: Get Reviews for a Book
@app.route("/api/book/<int:book_id>/reviews")
def api_reviews(book_id):
    reviews = db.execute(text("""
        SELECT r.rating, r.comment, u.username 
        FROM reviews r JOIN users u ON r.user_id = u.id 
        WHERE book_id = :book_id
    """), {"book_id": book_id}).fetchall()

    if not reviews:
        return jsonify({"error": "No reviews found"}), 404

    return jsonify([{"username": r.username, "rating": r.rating, "comment": r.comment} for r in reviews])

if __name__ == "__main__":
    app.run(debug=True)
