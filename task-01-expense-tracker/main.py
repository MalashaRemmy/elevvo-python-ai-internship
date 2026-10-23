"""Task 1: CLI Expense Tracker with Persistent JSON Storage.

A command-line expense tracker built with the Python standard library only.
Expenses are kept in a list of dictionaries in memory and persisted to a
local JSON file so they survive between program runs.
"""

import json
import math
import os
import sys
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.json")

MENU = """\
===== Expense Tracker =====
1. Add an expense
2. View all expenses
3. Generate a monthly summary
4. Exit
"""


class ExpenseStorageError(Exception):
    """Raised when expense data cannot be read or written safely."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_amount(raw_amount):
    """Return a positive amount rounded to two decimal places."""
    try:
        amount = float(raw_amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number (e.g. 12.50).")

    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    rounded_amount = round(amount, 2)

    if rounded_amount <= 0:
        raise ValueError("Amount must be at least 0.01.")

    return rounded_amount

def validate_category(raw_category):
    """Return the cleaned category name, or raise ValueError if blank."""
    category = raw_category.strip()
    if not category:
        raise ValueError("Category must not be empty.")
    return category

def validate_date(raw_date):
    """Return a valid date string in exact YYYY-MM-DD format."""
    text = raw_date.strip()

    if (
        len(text) != 10
        or text[4] != "-"
        or text[7] != "-"
        or not (text[:4] + text[5:7] + text[8:]).isdigit()
    ):
        raise ValueError("Date must be in YYYY-MM-DD format.")

    try:
        date.fromisoformat(text)
    except ValueError:
        raise ValueError("Date must be a valid calendar date in YYYY-MM-DD format.")

    return text

def validate_month(raw_month):
    """Return the month string in strict YYYY-MM format, or raise ValueError."""
    text = raw_month.strip()
    parts = text.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise ValueError("Month must be in YYYY-MM format (e.g. 2026-03).")
    year_text, month_text = parts
    if not (year_text.isdigit() and month_text.isdigit()):
        raise ValueError("Month must be in YYYY-MM format (e.g. 2026-03).")
    month_number = int(month_text)
    if not 1 <= month_number <= 12:
        raise ValueError("Month number must be between 01 and 12.")
    return text


# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------

def load_expenses(file_path=DATA_FILE):
    """Load expenses from a JSON file.

    Returns an empty list if the file does not exist. Raises
    ExpenseStorageError for malformed JSON or an unexpected data
    structure, so callers never silently overwrite user data.
    """
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ExpenseStorageError(
            f"'{file_path}' is not valid JSON: {exc}. "
            "The file was left untouched; please fix it manually."
        ) from exc
    except OSError as exc:
        raise ExpenseStorageError(f"Could not read '{file_path}': {exc}") from exc

    if not isinstance(data, list):
        raise ExpenseStorageError(
            f"'{file_path}' should contain a JSON array of expenses, "
            f"but found {type(data).__name__}. The file was left untouched."
        )
    for index, record in enumerate(data):
        if not is_valid_expense_record(record):
            raise ExpenseStorageError(
                f"Expense record at position {index} in '{file_path}' has an "
                "unexpected structure. The file was left untouched."
            )
    return data

def is_valid_expense_record(record):
    """Check that a record contains valid amount, category, and date fields."""
    if not isinstance(record, dict):
        return False

    if set(record.keys()) != {"amount", "category", "date"}:
        return False

    amount = record["amount"]
    if (
        not isinstance(amount, (int, float))
        or isinstance(amount, bool)
        or not math.isfinite(amount)
        or amount <= 0
    ):
        return False

    if not isinstance(record["category"], str) or not record["category"].strip():
        return False

    if not isinstance(record["date"], str):
        return False

    try:
        validate_date(record["date"])
    except ValueError:
        return False

    return True

def save_expenses(expenses, file_path=DATA_FILE):
    """Write expenses to the JSON file with readable indentation."""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(expenses, file, indent=2)
            file.write("\n")
    except OSError as exc:
        raise ExpenseStorageError(f"Could not write '{file_path}': {exc}") from exc


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def summarize_month(expenses, month):
    """Aggregate expenses for the given 'YYYY-MM' month.

    Returns a dictionary with the expense count, the total amount, and
    per-category totals and counts, from which averages are derived.
    """
    month = validate_month(month)
    selected = [e for e in expenses if e["date"].startswith(month + "-")]

    category_totals = {}
    category_counts = {}
    for expense in selected:
        category = expense["category"]
        category_totals[category] = category_totals.get(category, 0.0) + expense["amount"]
        category_counts[category] = category_counts.get(category, 0) + 1

    return {
        "month": month,
        "count": len(selected),
        "total": round(sum(e["amount"] for e in selected), 2),
        "category_totals": {k: round(v, 2) for k, v in category_totals.items()},
        "category_counts": category_counts,
    }


# ---------------------------------------------------------------------------
# CLI interaction
# ---------------------------------------------------------------------------

def prompt_for_expense():
    """Prompt until the user enters a fully valid expense; return it as a dict."""
    while True:
        try:
            amount = validate_amount(input("Amount: "))
            category = validate_category(input("Category: "))
            expense_date = validate_date(input("Date (YYYY-MM-DD): "))
        except ValueError as exc:
            print(f"Invalid input: {exc} Please try again.\n")
            continue
        return {"amount": amount, "category": category, "date": expense_date}


def add_expense(expenses):
    """Prompt for a valid expense, append it, and persist it."""
    expense = prompt_for_expense()
    expenses.append(expense)
    try:
        save_expenses(expenses)
    except ExpenseStorageError as exc:
        expenses.pop()  # keep memory and file consistent
        print(f"Error: {exc}")
        return
    print(f"Saved: {format_expense(expense)}")


def format_expense(expense):
    """Format one expense for display."""
    return f"{expense['date']}  {expense['category']:<20} ${expense['amount']:.2f}"


def view_expenses(expenses):
    """Display all expenses, or a clear message when there are none."""
    if not expenses:
        print("No expenses recorded yet.")
        return
    print(f"{'Date':<12}{'Category':<22}{'Amount':>10}")
    print("-" * 44)
    for expense in expenses:
        print(f"{expense['date']:<12}{expense['category']:<22}${expense['amount']:>9.2f}")


def show_monthly_summary(expenses):
    """Prompt for a month and display its summary report."""
    try:
        month = validate_month(input("Enter month (YYYY-MM): "))
    except ValueError as exc:
        print(f"Invalid input: {exc}")
        return

    summary = summarize_month(expenses, month)
    if summary["count"] == 0:
        print(f"No expenses recorded for {month}.")
        return

    print(f"\n===== Summary for {month} =====")
    print(f"Number of expenses: {summary['count']}")
    print(f"Total spending:     ${summary['total']:.2f}")
    print(f"{'Category':<22}{'Total':>10}{'Count':>7}{'Average':>12}")
    print("-" * 51)
    for category in sorted(summary["category_totals"]):
        total = summary["category_totals"][category]
        count = summary["category_counts"][category]
        average = total / count
        print(f"{category:<22}${total:>9.2f}{count:>7}${average:>11.2f}")


def main():
    """Run the interactive expense tracker."""
    try:
        expenses = load_expenses(DATA_FILE)
    except ExpenseStorageError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    while True:
        print(MENU)
        choice = input("Choose an option (1-4): ").strip()
        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            view_expenses(expenses)
        elif choice == "3":
            show_monthly_summary(expenses)
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 4.")
        print()


if __name__ == "__main__":
    main()