#imports the file books.csv into the books table in the project1 database


import csv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

# PostgreSQL connection
engine = create_engine("postgresql://postgres:Sea22%40%40S@localhost/project1")
db = scoped_session(sessionmaker(bind=engine))

def main():
    with open("books.csv") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row if present
        for isbn, title, author, year in reader:
            db.execute(text("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"),
                       {"isbn": isbn, "title": title, "author": author, "year": int(year)})  # ✅ Convert `year` to integer

    db.commit()  # ✅ Commit after all inserts

if __name__ == "__main__":
    main()
