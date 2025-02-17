# Project 1
By: Samuel Ethan Abastillas
UCID: 3009765

ENGO 551

Hello Everyone,

This is a simple webpage which requires users to register (register.html) a username and a password before proceeding.
If the user already has a account within the webpage, simply login to access the library of books. 

Make sure to download all required html templates within
the templates folder and the books.csv file in order for the webpage to fully work. Lastly, make sure to download flask (if not already installed) through the terminal using: 
 - py -3 -m venv .venv
 - .venv\Scripts\activate

To begin, run application.py through flask and go through the login page(login.html). Once inside the login page, search (search.html) for a books name, author,
isbn code or year that it was released. Then the user will be taken to a page which will show the books details and the user is also provided a button which will allow
the user to leave a review. All the reviews, users registered and books are stored within the project1 database through postgresql. The database url is also provided
within the application.py file along with valid credentials to simply use the webpage.

Make sure to install all required python packages contained inside of requirements.txt using: pip install -r requirements.txt. 
