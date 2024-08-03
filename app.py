from crypt import methods
import os
import sys

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter {Configuring Jinja}
app.jinja_env.filters["usd"] = usd
# Allows me to use Zip with Jinja, thus iterating over 2 Lists
app.jinja_env.filters['zip'] = zip

# # Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Set up session with SQLAlchemy
app.config['SESSION_SQLALCHEMY'] = db
Session(app)

# Configure Heroku to use Postgres database
# uri = os.getenv("DATABASE_URL")
# if uri.startswith("postgres://"):
#     uri = uri.replace("postgres://", "postgresql://")
# db = SQL(uri)

# db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Use SQLite3 to attain different Lists of Dictionaries to pass into Render Template
    sess_id = (session["user_id"])
    stocks_portfolio = db.engine.execute("SELECT * FROM stocks WHERE user_id = ?", sess_id)

    # Get User Cash
    user_cash_listdict = db.engine.execute("SELECT cash FROM users WHERE id = ?", sess_id)
    user_cash = user_cash_listdict[0]["cash"]

    # Calculate Individual Stock Total
    individual_stock_total = []
    # For each stock, assign the total (value) to the symbol (key)
    for jisho in stocks_portfolio:
        stock_symbol = jisho["symbol"]
        updated_stock = lookup(stock_symbol)
        updated_price = updated_stock["price"]
        total = jisho["shares_qty"] * updated_stock["price"]
        individual_stock_total.append({"symbol": stock_symbol, "total": total, "price": updated_price})

    # Calculate Total Assets
    total_assets = 0
    for jisho in individual_stock_total:
        total_assets += float(jisho["total"])

    total_assets += float(user_cash)

    return render_template("index.html", stocks_portfolio=stocks_portfolio, user_cash=user_cash, individual_stock_total=individual_stock_total, total_assets = total_assets)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # Purchasing Shares via POST
    if (request.method == "POST"):
        # Scrape User Input
        stock_symbol = request.form.get("symbol")
        # Handling Fractions
        try:
            stock_shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Shares must be positive", 400)
        stock_dict = lookup(stock_symbol)

        # Form Validation
        # Blank
        if (not stock_symbol):
            return apology("Symbol Field is empty!! Please provide a Symbol!!")
        # Non-Existent Symbol
        if (stock_dict == None):
            return apology("Stock Symbol does not exist!!")
        # Non-Positive Integer
        if (stock_shares <= 0):
            return apology("Please provide a positive number of shares to be purchased!!")

        # Purchasing Stocks
        stock_currentprice = stock_dict["price"]
        share_name = stock_dict["name"]

        # Determine Current User's Cash using their Session ID as it returns us a List of Dicts
        sess_id = (session["user_id"])
        cash_dict = db.engine.execute("SELECT cash FROM users WHERE id = ?", sess_id)
        # Same reason as sess_id
        # Cleaning Cash to be used
        user_cash = cash_dict[0]["cash"]

        # Determine if User can afford the shares
        transaction_cost = stock_currentprice * stock_shares
        if (transaction_cost > float(user_cash)):
            return apology("You are unable to complete this transaction due to insufficient funds!!")

        # Check if the User has bought this particular stock before (SELECT returns a List)
        first_time_buyer = len(db.engine.execute("SELECT stock_name FROM stocks WHERE user_id = ? AND symbol = ?", sess_id, stock_symbol))

        # Empty List as New Stock
        if (first_time_buyer == 0):
            # Record the Transaction
            db.engine.execute("INSERT INTO transactions (user_id, symbol, stock_name, purchased_price, shares_qty, datetime) VALUES (?, ?, ?, ?, ?, ?)",
            sess_id, stock_symbol, share_name, stock_currentprice, stock_shares, datetime.now())
            # Record the Account
            db.engine.execute("INSERT INTO stocks (user_id, symbol, stock_name, current_price, shares_qty) VALUES (?, ?, ?, ?, ?)",
            sess_id, stock_symbol, share_name, stock_currentprice, stock_shares)

        # Existing Stock
        else:
            # Record the Transaction
            db.engine.execute("INSERT INTO transactions (user_id, symbol, stock_name, purchased_price, shares_qty, datetime) VALUES (?, ?, ?, ?, ?, ?)",
                       sess_id, stock_symbol, share_name, stock_currentprice, stock_shares, datetime.now())
            # Update the Account
            old_qty_dict = db.engine.execute("SELECT shares_qty FROM stocks WHERE user_id = ?", sess_id)
            old_qty = old_qty_dict[0]["shares_qty"]
            new_qty = old_qty + stock_shares
            db.engine.execute("UPDATE stocks SET current_price = ?, shares_qty = ? WHERE user_id = ? AND symbol = ?",
                       stock_currentprice, new_qty, sess_id, stock_symbol)

        # Update User's Cash
        user_cash = user_cash - transaction_cost
        db.engine.execute("UPDATE users SET cash = ? WHERE id = ?", user_cash, sess_id)
        return redirect("/")

    # GET Request to reach Form
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # GET Request
    if (request.method == "GET"):
        sess_id = session["user_id"]
        stocks_portfolio = db.engine.execute("SELECT * FROM transactions WHERE user_id = ?", sess_id)
        return render_template("history.html", stocks_portfolio=stocks_portfolio)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.engine.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # If User submits a form
    if request.method == "POST":
        # Scrape User Input
        stock_symbol = request.form.get("symbol")

        # Use Lookup Function to get back a Dictionary
        stock_quote_dict = lookup(stock_symbol)
        # Error Checking
        if (stock_quote_dict == None):
            return apology("Sorry! The Stock Symbol provided does not exist!!!")
        # Determine name, price, symbol
        stock_name = stock_quote_dict["name"]
        stock_price = round(stock_quote_dict["price"], 2)  # Format as USD

        # Render the Quoted Template and Pass in the Necessary Values, formatted as USD within HTML file itself
        return render_template("quoted.html", name=stock_name, price=stock_price, symbol=stock_symbol)

    # GET Request
    else:
        # Display a Form to request a Stock Quote
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Register User and Insert into Database
    if request.method == "POST":
        # Store User Input
        new_username = request.form.get("username")  # Argument is Name of Input Tag
        new_password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if any field was left empty
        if (not new_username) or (not new_password) or (not confirmation):
            return apology("Please fill out all the fields required to be registered!!")
        # Check if Password and Confimation matches
        elif (new_password != confirmation):
            return apology("Please check that you have entered your password correctly!!")
        # Check if Username has been taken
        elif (db.engine.execute("SELECT * FROM users WHERE username = ?", new_username)):
            return apology("Username is in use. Please pick another!!", 400)

        # If no errors, add the User into our Database
        hashed_pw = generate_password_hash(new_password)
        db.engine.execute("INSERT INTO users (username, hash) VALUES(?,?)", new_username, hashed_pw)

        # Log User in
        session["user_id"] = (db.engine.execute("SELECT id FROM users WHERE username = ?", new_username))[0]['id']
        return redirect("/")

    # GET Request to go to Registration Form
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Submitting Sell Request
    if request.method == "POST":
        # Getting User Input
        shares_sell_qty = int(request.form.get("shares"))
        shares_sold_sym = request.form.get("symbol")

        # Input Validation
        sess_id = session["user_id"]
        shares_owned_dict = db.engine.execute("SELECT shares_qty FROM stocks WHERE user_id = ?", sess_id)
        shares_owned = shares_owned_dict[0]["shares_qty"]
        if (shares_sell_qty <= 0):
            # Non-Positive Number of Shares to be sold
            return apology("Please provide a positive number of shares to be sold!!!")
        elif (shares_sold_sym == None):
            # User does not own that stock or failed to select
            return apology("Shares to be sold was not selected!!!")
        elif (shares_sell_qty > shares_owned):
            # User does not have that many shares to sell
            return apology("Shares to be sold exceed the shares you own!!!")

        # Sell the Shares
        stock_quote = lookup(shares_sold_sym)
        current_price = stock_quote["price"]
        stock_name = stock_quote["name"]
        # Cash is in USD format, a string. Thus it needs to be stripped and replaced to be cast as a float
        current_cash = (db.engine.execute("SELECT cash FROM users WHERE id = ?", sess_id)[0]["cash"])

        if (shares_sell_qty == shares_owned):
            # Record Transaction for Sale
            sold_shares = -(shares_sell_qty)
            db.engine.execute("INSERT INTO transactions (user_id, symbol, stock_name, purchased_price, shares_qty, datetime) VALUES (?, ?, ?, ?, ?, ?)",
                        sess_id, shares_sold_sym, stock_name, current_price, sold_shares, datetime.now())
            # Remove the Entire Record from TABLE stocks
            db.engine.execute("DELETE FROM stocks WHERE stock_name = ?", stock_name)

        else:
            # Record Transaction for Sale
            sold_shares = -(shares_sell_qty)
            db.engine.execute("INSERT INTO transactions (user_id, symbol, stock_name, purchased_price, shares_qty, datetime) VALUES (?, ?, ?, ?, ?, ?)",
                        sess_id, shares_sold_sym, stock_name, current_price, sold_shares, datetime.now())
            # Update the Record
            new_shares_owned = shares_owned - shares_sell_qty
            db.engine.execute("UPDATE stocks SET shares_qty = ? WHERE user_id = ? AND symbol = ?",
            new_shares_owned, sess_id, shares_sold_sym)

        # Update Cash
        cash_gain = float(current_price * shares_sell_qty)
        current_cash += cash_gain
        db.engine.execute("UPDATE users SET cash = ? WHERE id = ?", current_cash, sess_id)

        return redirect("/")

    # GET Request to get to Sell Page
    else:
        # Cookies
        sess_id = session["user_id"]

        # Get a List of Dictionaries of Stocks owned
        stocks_portfolio = db.engine.execute("SELECT symbol FROM stocks WHERE user_id = ?", sess_id)
        return render_template("sell.html", stocks_portfolio=stocks_portfolio)

@app.route("/add", methods=["GET","POST"])
@login_required
def add_cash():
    """Add Cash to Wallet"""
    if (request.method == "POST"):
        # Get User Input
        funds_added = float(request.form.get("add_funds"))

        # Input Validation {Empty Field, Negative Value Given}
        if (funds_added == None):
            # Empty Field
            return apology("Please indicate an amount to top up your account!!", 406)
        elif (funds_added <= 0):
            return apology("You have to indicate a positive amount of funds to be added!!!", 406)

        # Determine Current Cash Flows
        sess_id = session["user_id"]
        # Execute SELECT returns a List of Dicts
        old_balance = (db.engine.execute("SELECT cash FROM users WHERE id = ?", sess_id))[0]["cash"]

        # Update New Cash Amount
        new_balance = old_balance + funds_added
        db.engine.execute("UPDATE users SET cash = ? WHERE id = ?", new_balance, sess_id)
        return redirect("/")

    # GET Request to reach form to add cash
    else:
        return render_template("add.html")

@app.route("/account", methods=["GET","POST"])
@login_required
def pass_change():
    # POST Request
    if request.method == "POST":
        # Take User Input
        old_pass_user = request.form.get("old_password")
        new_pass = request.form.get("new_password")
        confirmation = request.form.get("new_confirmation")
        sess_id = session["user_id"]

        # Form Validation
        if old_pass_user == None:
            return apology("Please submit all the Password Fields or we cannot change the Password for you!!", 403)
        # Wrong Old Password
        # Select returns a List of Dicts
        hash_pass_dict = db.engine.execute("SELECT hash FROM users WHERE id = ?", sess_id)

        if not check_password_hash(hash_pass_dict[0]["hash"], old_pass_user):
            return apology("You have provided the wrong current password!!", 403)
        # Passwords do not match
        if new_pass != confirmation:
            return apology("Please ensure your passwords matches!!", 403)
        
        # Changing of Password
        db.engine.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new_pass), sess_id)
        return redirect("/")

    # GET Request
    else:
        return render_template("account.html")