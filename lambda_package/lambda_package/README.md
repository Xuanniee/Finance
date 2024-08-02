# Finance (Flask)

## Project Description
![Picture of Homepage](./Images/Homepage.png?raw=true "HomePage")
Finance (Flask) is a web application that provides the ability to conduct paper trading, by allowing users to "buy" & "sell" stocks. The aim of the web application is to promote personal finance and encourage investing amongst young adults by allowing them to build up experience.

## Content

### 1. User Authentication
![Picture of Registration](./Images/Register.png?raw=true "Registration")
Upon visiting the web application, visitors will be asked to authenticate themselves to be able to use the services offered by the web application. Visitors without an account can create an account via the navlink on the top right corner of the webpage.

Users will only need to provide a Username and Password to create an account as this is only to create sessions for different users to track their investing progress. The account is created by making a POST Request to store the User's details, including a hash of the password, in the database. Once an account is created or the user is logged in, they will be redirected to the Index Page. [Do note that as this is for learning purposes, the database used is SQLite3 and thus not suitable for heavy usage]

![Picture of Register Error](./Images/Register%20Error.png?raw=true "Register Error")
If the User were to leave any of the fields empty, an error message will be rendered to the user in the form of a picture as depicted above. Alternatively, if the passwords do not match, a similar error message will be prompted.

### 2. Index Page
![Picture of Index Page](./Images/Index%20Page.png?raw=true "Index Page")
At the Index page, Users are able to view several information about their stock portfolio:

* Name of the Shares owned
* Quantity of Shares owned
* Price of the Share owned
* Total Value of the Shares owned
* Total Value of Cash remaining
* Total Value of all their Assets

Using the Navbar on top of the web application, Users are able to access several features:

* Stock Quotation
* Buy Stocks
* Sell Stocks
* See Transactions
* Top up Cash into their Accounts
* Feeling Lucky
* Account Settings
* Log Out

### 3. Stock Quotation
![Picture of Quote Form](./Images/Quote%20Form.png?raw=true "Quote Form")
Upon clicking the Quote Button, Users will be redirected to a view containing a form for them to input the stock symbol of the companies they are interested in. This will then query and provide more information to the User for them to make an informed decision about a stock.

![Picture of Quote Results](./Images/Quote%20Result.png?raw=true "Quote Results")
To illustrate, a User inputting AAPL will return the current market value of Apple's Shares as shown above.

### 4. Buying Stocks
![Picture of Buy Form](./Images/Buy%20Form.png?raw=true "Buy Form")
To buy shares, Users will have to input the Stock Symbol and the Quantity of Shares they would like to buy. If any of the fields are empty, invalid, or if the User cannot afford the shares, an error message will be rendered to Users like before. 

They will then be redirected to the index page to see all the shares they have purchased.

### 5. Selling Stocks
![Picture of Sell Form](./Images/Sell%20Form.png?raw=true "Sell Form")
Similar to the Buy Form, Users will have to indicate the Symbol and Quantity to sell their shares. However, the Symbol will be in a dropdown list as Users should not be able to sell stocks that they do not yet possess. Once the shares are sold, they will be redirected to the Index Page as well.

### 6. Transaction History
![Picture of Transactions](./Images/History.png?raw=true "Transactions")
Upon clicking History, Users will be redirected to a view that presents all of the transactions made by the User in reverse chronological order as shown above. The sign of the quantity will indicate if the transaction was a Buy or Sell.

### 7. Additional QOL Features
![Picture of Add Cash](./Images/Add%20Cash.png?raw=true "Add Cash")
Users are also able to top up more cash into their account if their funds are running low.

![Picture of Change Password](./Images/Change%20Password.png?raw=true "Change Password")
Users can also change their password if they like.

## Learning Outcomes

* Learnt and Familiarised with the Flask Framework.
* Learnt the Model-View-Controller Framework via Flask.
* Learnt Jinja Templating.
* Learnt to work with Forms in HTML.
* Learnt how to use Flask Templates to factor out repeated HTML code.
* Learnt about GET & POST Requests.
* Learnt how to integrate SQLite3 with Flask.
* Deploying a Web Application on Heroku.

## URL Application is hosted on
https://panpan-finance.herokuapp.com/