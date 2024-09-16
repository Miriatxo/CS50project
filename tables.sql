--CREATED
CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

-- CREATED
CREATE TABLE Income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL NOT NULL,
    source TEXT,
    comment TEXT,
    date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- CREATED
CREATE TABLE Expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    category TEXT,
    comment TEXT,
    date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- The June expenses from the food category
SELECT amount, description, comment, date
FROM expenses
WHERE user_id = ?
AND category = "food"
AND strftime('%m', date) = '06'
ORDER BY date;

-- NOT CREATED --
CREATE TABLE PasswordResets (
    email TEXT,
    token TEXT,
    expires DATETIME
);
