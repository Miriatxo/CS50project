import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from itertools import chain


# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///tables.db")

@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id:
        return redirect('/dashboard')
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate form inputs
        if not username or not password:
            flash('All fields are required!')
            return redirect('/register')

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect('/register')

        # Check if username already exists
        existing_user = db.execute("SELECT * FROM Users WHERE username = ?", username)
        if existing_user:
            flash('Username already taken. Please choose a different one.')
            return redirect('/register')

        # Generate password hash
        hashed_password = generate_password_hash(password)

        try:
            # Insert new user into the Users table
            db.execute("INSERT INTO Users (username, password) VALUES(?, ?)", username, hashed_password)

            # Get the user ID of the newly created user
            user = db.execute("SELECT id FROM Users WHERE username = ?", username)[0]

            if user:
                # Store the user ID and username in the session
                session['user_id'] = user['id']
                session['username'] = username
                return redirect('/dashboard')
            else:
                flash('User could not be found after registration.')
                return redirect('/register')

        except Exception as e:
            print(f"An error occurred: {e}")
            flash('An error occurred during registration. Please try again.')
            return redirect('/register')

    return render_template('register.html')


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')
    username = session.get('username')

    if request.method == 'POST':
        # Retrieve the user from the database
        user = db.execute("SELECT * FROM Users WHERE id = ?", user_id)

        if not user:
            flash('User not found.')
            return redirect('/change_password')

        old_password = request.form.get('old_password')

        # Check if old_password matches the current password
        if not check_password_hash(user[0]['password'], old_password):
            flash('Current password is incorrect.')
            return redirect('/change_password')

        new_password = request.form.get('new_password')
        confirmation = request.form.get('confirmation')

        # Check if new password matches the confirmation
        if new_password != confirmation:
            flash('New password and confirmation do not match.')
            return redirect('/change_password')

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        try:
            # Update user's password in the Users table
            db.execute("UPDATE Users SET password = ? WHERE id = ?", hashed_password, user_id)
            flash('Password successfully changed.')
            return redirect('/dashboard')

        except Exception as e:
            print(f"An error occurred: {e}")
            flash('An error occurred during password change.')
            return redirect('/change_password')

    return render_template('change_password.html', username=username)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.')
            return redirect('/login')

        # Query for user in the database
        user = db.execute('SELECT * FROM Users WHERE username = ?', username)

        if user:
            user = user[0]  # Get the first user (there should only be one)
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']  # Store username in session
                return redirect('/dashboard')

        flash('Invalid username and/or password.')
        return redirect('/login')

    return render_template('login.html')


@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the login page or home page
    return redirect('/')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')
    username = session.get('username')

    # Get the current month
    month = datetime.now().strftime('%Y-%m')

    # Create date in user-friendly format for pie chart title
    formatted_month = datetime.strptime(month, "%Y-%m").strftime("%B %Y")

    try:
        # Get user's income and expenses for the selected month
        income_result = db.execute("SELECT SUM(amount) as total FROM Income WHERE user_id = ? AND strftime('%Y-%m', date) = ?", user_id, month)
        expense_result = db.execute("SELECT SUM(amount) as total FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?", user_id, month)

        # Handle cases where results are None
        income_total = income_result[0]['total'] if income_result and income_result[0]['total'] is not None else 0
        expense_total = expense_result[0]['total'] if expense_result and expense_result[0]['total'] is not None else 0

        # Calculate current balance and get formatted balance (2 decimal points)
        balance = income_total - expense_total
        formatted_balance = "{:.2f}".format(balance)

        # Calculate what percentage of the budget the current balance represents
        percentage = int((balance * 100) / income_total) if income_total != 0 else 0

        # Get user's selection regarding how to sort expenses table
        order_by = request.args.get('order_by', 'date')

        # Query the expenses based on the selected order
        if order_by == 'category':
            # Query to get expenses for the selected month sorted by category
            expenses = db.execute("SELECT * FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY category", user_id, month)
        else:
            # Query to get expenses for the selected month sorted by date
            expenses = db.execute("SELECT * FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY date DESC", user_id, month)

        # Handle empty results for expenses
        expenses = expenses if expenses else []

        # Query to get expense totals by category (this is the same regardless of order_by)
        category_totals = db.execute("SELECT category, SUM(amount) as total FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? GROUP BY category", user_id, month)

        # Create a dictionary of expense categories and their totals
        categories = {item['category']: item['total'] if item['total'] is not None else 0 for item in category_totals} if category_totals else {}

        # Render the dashboard template with the relevant data
        return render_template('dashboard.html',
                       expenses=expenses,
                       expense_total=expense_total,
                       categories=categories,
                       income_total=income_total,
                       formatted_month=formatted_month,
                       balance=formatted_balance,
                       percentage=percentage,
                       username=username,
                       has_expenses=bool(expenses)) # Pass flag for no expenses (just to illustrate for my future self this alternative method of handling charts and tables when no data, like in the history and analytics routes; different approach: view_income and view_expenses)

    except Exception as e:
        print("Error occurred while accessing dashboard:", str(e))
        flash("An error occurred while trying to access the dashboard. Please try again later.")
        return redirect('/dashboard')


@app.route('/add_income', methods=['POST'])
def add_income():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')

    amount = request.form.get('amount')
    source = request.form.get('source', '').capitalize()
    comment = request.form.get('comment', '').capitalize()
    date_input = request.form.get('date', '')

    if date_input:
        date = datetime.strptime(date_input, '%Y-%m-%d')
    else:
        date = datetime.now().date()

    # Require amount
    try:
        if not amount or amount.strip() == '':
            flash("Amount cannot be empty")
            return redirect('/add_income')
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be greater than 0")
            return redirect('/add_income')
    except ValueError:
        flash("Amount must be a number")
        return redirect('/add_income')

    # Insert new income into the Income table
    try:
        db.execute('INSERT INTO Income (user_id, amount, source, comment, date) VALUES (?, ?, ?, ?, ?)', user_id, amount, source, comment, date)
        flash("Income added successfully.")
    except Exception as e:
        print("Error occurred while adding income:", str(e))
        flash("An error occurred while adding the income. Please try again.")

    return redirect('/dashboard')


@app.route('/delete_income/<int:income_id>', methods=['POST'])
def delete_income(income_id):
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')

    try:
        db.execute('DELETE FROM Income WHERE id = ? AND user_id = ?', income_id, user_id)
        flash("Income added successfully.")
    except Exception as e:
        print("Error occurred while deleting income:", str(e))
        flash("An error occurred while trying to delete the income record.")

    return redirect('/view_income')

@app.route('/view_income', methods=['GET'])
def view_income():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')
    username = session.get('username')

    # Get the month of the history page (through the link's URL) or default to the current month
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    formatted_month = datetime.strptime(month, "%Y-%m").strftime("%B %Y")

    try:
        # Get user's income total for the month
        income_result = db.execute("SELECT SUM(amount) as total FROM Income WHERE user_id = ? AND strftime('%Y-%m', date) = ?", user_id, month)

        # Handle cases where results are None
        income_total = income_result[0]['total'] if income_result and income_result[0]['total'] is not None else 0

        # Query to get incomes for the month sorted by date
        incomes = db.execute("SELECT * FROM Income WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY date DESC", user_id, month)

        # Handle empty results
        incomes = incomes if incomes else []

        return render_template('view_income.html',
                           formatted_month=formatted_month,
                           income_total=income_total,
                           incomes=incomes,
                           username=username)

    except Exception as e:
        print("Error occurred while viewing income:", str(e))
        flash("An error occurred while trying to view income records. Please try again later.")
        return redirect('/view_income')


@app.route('/add_expense', methods=['POST'])
def add_expense():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')

    amount = request.form.get('amount')
    description = request.form.get('description', '').capitalize()
    category = request.form.get('category')
    comment = request.form.get('comment', '').capitalize()
    date_input = request.form.get('date', '')

    # Validate amount
    try:
        if not amount or amount.strip() == '':
            flash("Amount cannot be empty")
            return redirect('/add_expense')
        amount = float(amount)
    except ValueError:
        flash("Amount must be a number")
        return redirect('/add_expense')

    # Validate category
    if not category:
        flash("Category cannot be empty")
        return redirect('/add_expense')

    if date_input:
        try:
            date = datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.")
            return redirect('/dashboard')
    else:
        date = datetime.now().date()

    # Insert new expense into the Expenses table
    try:
        db.execute('INSERT INTO Expenses (user_id, amount, description, category, comment, date) VALUES (?, ?, ?, ?, ?, ?)', user_id, amount, description, category, comment, date)
        flash("Expense added successfully.")
    except Exception as e:
        print("Error occurred while adding expense:", str(e))
        flash("An error occurred while adding the expense. Please try again.")

    return redirect('/dashboard')


@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')

    source = request.form.get('source')

    try:
        db.execute('DELETE FROM Expenses WHERE id = ? AND user_id = ?', expense_id, user_id)
        flash("Expense deleted successfully.")
    except Exception as e:
        print("Error occurred while deleting expense:", str(e))
        flash("An error occurred while trying to delete the expense record.")

    if source == 'view_expenses':
        return redirect('/view_expenses')
    elif source == 'dashboard':
        return redirect('/dashboard')

@app.route('/view_expenses', methods=['GET'])
def view_expenses():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')
    username = session.get('username')

    # Get the month of the history page (through history page link to view_expenses) or default to the current month
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    formatted_month = datetime.strptime(month, "%Y-%m").strftime("%B %Y")

    try:
        # Get user's expenses total for the month
        expense_result = db.execute("SELECT SUM(amount) as total FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?", user_id, month)

        # Handle cases where results are None
        expense_total = expense_result[0]['total'] if expense_result and expense_result[0]['total'] is not None else 0

        # Get user's selection regarding how to sort expenses table
        order_by = request.args.get('order_by', 'date')

        # Query the expenses based on the selected order
        if order_by == 'category':
            # Query to get expenses for the selected month sorted by category
            expenses = db.execute("SELECT * FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY category", user_id, month)
        else:
            # Query to get expenses for the selected month sorted by date
            expenses = db.execute("SELECT * FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY date DESC", user_id, month)

        # Handle empty results for expenses
        expenses = expenses if expenses else []

        # Query to get expense totals by category (this is the same regardless of order_by)
        category_totals = db.execute("SELECT category, SUM(amount) as total FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? GROUP BY category", user_id, month)

        # Create a dictionary of expense categories and their totals
        categories = {item['category']: item['total'] if item['total'] is not None else 0 for item in category_totals} if category_totals else {}

        return render_template('view_expenses.html',
                               formatted_month=formatted_month,
                               expense_total=expense_total,
                               expenses=expenses,
                               categories=categories,
                               username=username)

    except Exception as e:
        print(f"Error while retrieving expenses: {e}")
        flash("An error occurred while fetching the expenses. Please try again.")
        return redirect('/dashboard')


@app.route('/history', methods=['GET', 'POST'])
def history():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')
    username = session.get('username')

    # If a month other than the current month is selected, redirect to the history page with the selected month in query parameters
    if request.method == 'POST':
        selected_month = request.form.get('month')
        return redirect(f'/history?month={selected_month}')

    # If no month is selected, default to the current month
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    try:
        # Get user's income and expenses for the selected month
        income_result = db.execute("SELECT SUM(amount) as total FROM Income WHERE user_id = ? AND strftime('%Y-%m', date) = ?", user_id, selected_month)
        expense_result = db.execute("SELECT SUM(amount) as total FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?", user_id, selected_month)

        # Handle cases where results are None
        income_total = income_result[0]['total'] if income_result and income_result[0]['total'] is not None else 0
        expense_total = expense_result[0]['total'] if expense_result and expense_result[0]['total'] is not None else 0

        # Calculate current balance and get formatted balance (2 decimal points)
        balance = income_total - expense_total
        formatted_balance = "{:.2f}".format(balance)

        # Query to get expenses for the selected month sorted by date
        expenses = db.execute("SELECT * FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY date DESC", user_id, selected_month)

        # Handle empty results for expenses
        expenses = expenses if expenses else []

        # Query to get expense totals by category
        category_totals = db.execute("SELECT category, SUM(amount) as total FROM Expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? GROUP BY category", user_id, selected_month)

        # Create a dictionary of expense categories and their totals
        categories = {item['category']: item['total'] if item['total'] is not None else 0 for item in category_totals} if category_totals else {}

        # Query to get income for the selected month sorted by date
        incomes = db.execute("SELECT * FROM Income WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY date DESC", user_id, selected_month)

        # Handle empty results
        incomes = incomes if incomes else []

        # Format the selected month for display
        formatted_month = datetime.strptime(selected_month, "%Y-%m").strftime("%B %Y")

        # Check if there are no expenses or incomes for the selected month
        has_data = bool(income_total or expense_total)

        # Render the history template with the relevant data
        return render_template('history.html',
                               expenses=expenses,
                               incomes=incomes,
                               income_total=income_total,
                               expense_total=expense_total,
                               formatted_balance=formatted_balance,
                               categories=categories,
                               selected_month=selected_month,
                               formatted_month=formatted_month,
                               has_data=has_data,
                               username=username)

    except Exception as e:
        # Print the exception for debugging
        print(f"Error while retrieving history: {e}")
        flash("An error occurred while retrieving history. Please try again.")
        return redirect('/history')


@app.route('/analytics', methods=['GET'])
def analytics():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session.get('user_id')
    username = session.get('username')

    # Get query parameters for start_date, end_date, and category
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    selected_category = request.args.get('category', None)

    try:
        # Handle start_date
        if not start_date:
            earliest_date_result = db.execute(
                "SELECT MIN(date) as min_date FROM (SELECT date FROM Income WHERE user_id = ? UNION SELECT date FROM Expenses WHERE user_id = ?)",
                user_id, user_id
            )
            start_date = earliest_date_result[0]['min_date'] if earliest_date_result[0]['min_date'] else datetime.now().strftime('%Y-%m-%d')

        # Handle end_date
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Parse the dates, handling potential time component
        start_date_obj = datetime.strptime(start_date.split()[0], '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date.split()[0], '%Y-%m-%d')

        # Format dates for display
        formatted_start_date = start_date_obj.strftime('%B %d, %Y')
        formatted_end_date = end_date_obj.strftime('%B %d, %Y')

        # Convert dates back to strings for SQL queries
        start_date_str = start_date_obj.strftime('%Y-%m-%d')
        end_date_str = end_date_obj.strftime('%Y-%m-%d')

        # Fetch detailed income and expense records
        expenses = db.execute(
            "SELECT * FROM Expenses WHERE user_id = ? AND DATE(date) BETWEEN ? AND ? ORDER BY date DESC",
            user_id, start_date_str, end_date_str
        )

        # Handle empty results for expenses
        expenses = expenses if expenses else []

        incomes = db.execute(
            "SELECT * FROM Income WHERE user_id = ? AND DATE(date) BETWEEN ? AND ? ORDER BY date DESC",
            user_id, start_date_str, end_date_str
        )

        # Handle empty results for incomes
        incomes = incomes if incomes else []

        # Create dictionaries from incomes and expenses
        income_dict = {str(item['date'])[:10]: item['amount'] for item in incomes}
        expense_dict = {str(item['date'])[:10]: item['amount'] for item in expenses}

        # Extract dates for the x-axis of the line chart
        income_dates = [str(item['date'])[:10] for item in incomes]
        # Extract income amounts
        income_values = [item['amount'] for item in incomes]

        # Extract dates for the x-axis
        expense_dates = [str(item['date'])[:10] for item in expenses]
        # Extract expense amounts
        expense_values = [item['amount'] for item in expenses]

        # Convert date strings to date objects for proper comparison
        income_dates = [datetime.strptime(date, "%Y-%m-%d") for date in income_dates]
        expense_dates = [datetime.strptime(date, "%Y-%m-%d") for date in expense_dates]

        # Merge income_dates and expense_dates, removing duplicates, to create a unified set of date labels for the line chart
        all_dates = sorted(set(chain(income_dates, expense_dates)))

        # Prepare income and expense values aligned with the unified dates
        income_values_aligned = [income_dict.get(date.strftime("%Y-%m-%d"), 0) for date in all_dates]
        expense_values_aligned = [expense_dict.get(date.strftime("%Y-%m-%d"), 0) for date in all_dates]

        # Convert the unified dates back to strings for the template
        all_dates_str = [date.strftime("%Y-%m-%d") for date in all_dates]

        # Calculate and format the totals and balance
        income_total = sum([item['amount'] for item in incomes])
        formatted_income_total = "{:.2f}".format(income_total)
        expense_total = sum([item['amount'] for item in expenses])
        formatted_expense_total = "{:.2f}".format(expense_total)
        balance = income_total - expense_total
        formatted_balance = "{:.2f}".format(balance)

        # If user selects category filter, query to get expenses grouped by month for the selected category
        if selected_category:
            monthly_expenses_by_category = db.execute(
                """
                SELECT
                    strftime('%Y-%m', date) AS month,
                    SUM(amount) AS total
                FROM Expenses
                WHERE user_id = ? AND category = ? AND DATE(date) BETWEEN ? AND ?
                GROUP BY month
                ORDER BY month ASC;
                """,
                user_id, selected_category, start_date_str, end_date_str
            )

            # Ensure monthly_expenses_by_category is not None before iterating over it
            if monthly_expenses_by_category is None:
                flash("Unable to retrieve data for the selected category.")
                return render_template(
                    'analytics.html',
                    expenses=expenses,
                    incomes=incomes,
                    income_total=income_total,
                    expense_total=expense_total,
                    formatted_balance=formatted_balance,
                    categories=categories if not selected_category else None,  # Only pass categories if no category is selected
                    category_totals=category_totals if not selected_category else None,  # Only pass if no category is selected
                    expense_months=expense_months if selected_category else None,  # Pass months for selected category
                    expense_totals_by_month=expense_totals_by_month if selected_category else None,  # Pass monthly totals
                    highest_expense=highest_expense if selected_category else None,
                    lowest_expense=lowest_expense if selected_category else None,
                    average_expense=average_expense if selected_category else None,
                    start_date=start_date,
                    end_date=end_date,
                    formatted_start_date=formatted_start_date,
                    formatted_end_date=formatted_end_date,
                    selected_category=selected_category,
                    username=username,
                    category_names=category_names if not selected_category else None,
                    has_data=has_data,
                    income_values_aligned=income_values_aligned,
                    expense_values_aligned=expense_values_aligned,
                    all_dates_str=all_dates_str
                )

            # Prepare data for the doughnut chart
            expense_months = [item['month'] for item in monthly_expenses_by_category]
            expense_totals_by_month = [item['total'] for item in monthly_expenses_by_category]

            if expense_totals_by_month:
                highest_expense = "{:.2f}".format(max(expense_totals_by_month))
                lowest_expense = "{:.2f}".format(min(expense_totals_by_month))
                average_expense = "{:.2f}".format(sum(expense_totals_by_month) / len(expense_totals_by_month))
            else:
                highest_expense = lowest_expense = average_expense = None

        # If no category is selected, just get the regular expenses by category
        else:
            highest_expense = lowest_expense = average_expense = None

            # Summarize expenses by category
            category_values = db.execute(
                "SELECT category, SUM(amount) as total FROM Expenses WHERE user_id = ? AND DATE(date) BETWEEN ? AND ? GROUP BY category",
                user_id, start_date_str, end_date_str
            )

            # Prepare data for template rendering
            categories = [{'category': item['category'], 'total': item['total']} for item in category_values]
            category_totals = [item['total'] if item['total'] is not None else 0 for item in category_values]

            # Extract category names for dougnut chart labels
            category_names = [category['category'] for category in categories]
        # Debug
        for i, (date, value) in enumerate(zip(expense_dates, expense_values)):
            print(f"Expense Date: {date}, Value: {value}")

        has_data = bool(incomes or expenses)

        if not (incomes or expenses):
            flash("No data available for the selected date range.")
            return render_template(
                'analytics.html',
                expenses=expenses,
                incomes=incomes,
                income_total=income_total,
                expense_total=expense_total,
                formatted_balance=formatted_balance,
                categories=categories if not selected_category else None,  # Only pass categories if no category is selected
                category_totals=category_totals if not selected_category else None,  # Only pass if no category is selected
                expense_months=expense_months if selected_category else None,  # Pass months for selected category
                expense_totals_by_month=expense_totals_by_month if selected_category else None,  # Pass monthly totals
                highest_expense=highest_expense if selected_category else None,
                lowest_expense=lowest_expense if selected_category else None,
                average_expense=average_expense if selected_category else None,
                start_date=start_date,
                end_date=end_date,
                formatted_start_date=formatted_start_date,
                formatted_end_date=formatted_end_date,
                selected_category=selected_category,
                username=username,
                category_names=category_names if not selected_category else None,
                has_data=has_data,
                income_values_aligned=income_values_aligned,
                expense_values_aligned=expense_values_aligned,
                all_dates_str=all_dates_str
            )


        # Render the analytics template
        return render_template(
            'analytics.html',
            expenses=expenses,
            incomes=incomes,
            income_total=income_total,
            expense_total=expense_total,
            formatted_balance=formatted_balance,
            categories=categories if not selected_category else None,  # Only pass categories if no category is selected
            category_totals=category_totals if not selected_category else None,  # Only pass if no category is selected
            expense_months=expense_months if selected_category else None,  # Pass months for selected category
            expense_totals_by_month=expense_totals_by_month if selected_category else None,  # Pass monthly totals
            highest_expense=highest_expense if selected_category else None,
            lowest_expense=lowest_expense if selected_category else None,
            average_expense=average_expense if selected_category else None,
            start_date=start_date,
            end_date=end_date,
            formatted_start_date=formatted_start_date,
            formatted_end_date=formatted_end_date,
            selected_category=selected_category,
            username=username,
            category_names=category_names if not selected_category else None,
            has_data=has_data,
            income_values_aligned=income_values_aligned,
            expense_values_aligned=expense_values_aligned,
            all_dates_str=all_dates_str
        )

    except Exception as e:
        print("Error occurred:", str(e))
        flash("An unexpected error occurred. Please try again later.")
        return redirect('/analytics')


if __name__ == '__main__':
    app.debug = True
    app.run()
