# PERSONAL EXPENSE TRACKER

#### Video Demo: https://youtu.be/1A8LgqtSc7Y

#### Introduction:

This expense tracker is a web-based Flask application designed to help manage and track personal expenses. It generates intuitive charts to provide insights into spending habits, helping you plan your finances better.

#### Description:

This application allows you to register with a username, email, and password to access your personal area where you can manage your expenses. There are login and logout pages to secure access, and you can change your password.

**Dashboard:**

When you enter your account, you are directed to the dashboard, which displays the current month's income, expenses, and net balance, as well as a form to add incomes and another to add expenses, a pie chart with the expense totals per category, and a table with the expenses of the present month. By default, the expenses table is ordered by date, but you can choose to order it by category.

From the dashboard, you can enter, view, and delete expenses and incomes. For each expense, you must enter the amount and choose a category. There are seven categories: Housing, Bills & Utilities, Food, Transportation, Shopping, Entertainment, and Others. Optionally, you can also enter the expense's description - for example, "lunch in town" - and a comment, such as "Dave owes me half". The current date is automatically included in the Expenses table row when the expense is created, but you can specify a different date, present or future, when you create the expense.

Regarding the form to add an income, the only field that you are required to fill in is the amount field, and you can additionally add a source, comment, and date - if the date is different from the current date.

**History:**

The History page shows a bar chart displaying the expense total and income total for the present month, together with a summary that includes the corresponding incomes and expenses tables, and the net balance, green if positive, red if negative. You can choose to see the records of any month.

**Analytics:**

The Analytics page shows a bar chart displaying the expense total and income total from the first transaction you entered to the present date, together with a summary that includes the corresponding income and expense totals, the net balance - green if positive, red if negative -, a line chart with the expenses and incomes per date, and a doughnut chart with the expense totals per category. You can select the date range you desire. And you can select a category, in which case the doughnut chart will display that category's expense totals per month, with the highest, lowest, and average monthly expenses in that category.

#### Technologies Used:

- Python
- Flask
- Jinja
- JavaScript
- HTML
- CSS
- Bootstrap
- SQLite
- Chart.js (for data visualization)



