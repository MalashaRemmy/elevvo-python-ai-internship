# CLI Expense Tracker

A command-line expense tracker built with Python. The application records expenses, stores them in a JSON file, and generates monthly spending summaries.

## Features

- Add an expense with an amount, category, and date.
- View all recorded expenses.
- Generate monthly summaries showing total spending and category breakdowns.
- Validate amounts, categories, dates, and stored records.
- Persist expenses in `expenses.json`.
- Handle missing or malformed storage files without silently overwriting invalid data.

## Requirements

- Python 3.12 or compatible Python 3 version
- No third-party runtime packages required

## Run the application

From this directory, run:

```bash
python main.py
```

The menu allows you to add expenses, view recorded expenses, generate a monthly summary, or exit the application.

## Data storage

Expenses are stored in `expenses.json` in this project directory. Each record contains:

- `amount`: a positive numeric expense amount rounded to two decimal places
- `category`: the expense category
- `date`: a valid date in `YYYY-MM-DD` format

Example record:

```json
[
  {
    "amount": 25.5,
    "category": "Transport",
    "date": "2026-03-15"
  }
]
```

## Run the tests

The test suite uses pytest. Install it if necessary:

```bash
python -m pip install pytest
```

Run the tests from this directory:

```bash
python -m pytest tests/test_expenses.py -v
```

The tests cover input validation, JSON persistence, invalid stored records, and monthly summaries.
