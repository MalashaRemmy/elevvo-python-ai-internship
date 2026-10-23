"""Automated tests for the Task 1 CLI expense tracker.

All tests use pytest's tmp_path fixture so the real expenses.json file
is never touched.
"""

import json

import pytest

import main


# ---------------------------------------------------------------------------
# 1. Valid expense creation / validation
# ---------------------------------------------------------------------------

def test_valid_expense_fields_are_accepted():
    assert main.validate_amount("12.50") == 12.50
    assert main.validate_category("  Food  ") == "Food"
    assert main.validate_date("2026-03-15") == "2026-03-15"


# ---------------------------------------------------------------------------
# 2. Invalid amounts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["0", "0.0", "0.001", "0.004", "-5", "-0.01", "", "abc", "12,50", "NaN", "inf"])
def test_invalid_amounts_are_rejected(raw):
    with pytest.raises(ValueError):
        main.validate_amount(raw)


# ---------------------------------------------------------------------------
# 3. Blank categories
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_blank_categories_are_rejected(raw):
    with pytest.raises(ValueError):
        main.validate_category(raw)


# ---------------------------------------------------------------------------
# 4. Valid and impossible dates
# ---------------------------------------------------------------------------

def test_valid_dates_are_accepted():
    assert main.validate_date("2024-02-29") == "2024-02-29"  # leap year
    assert main.validate_date("2026-12-31") == "2026-12-31"


@pytest.mark.parametrize("raw", ["20261023", "2026-02-30", "2026-13-01", "2025-02-29",
                                 "15-03-2026", "2026/03/15", "not-a-date"])
def test_impossible_or_misformatted_dates_are_rejected(raw):
    with pytest.raises(ValueError):
        main.validate_date(raw)


# ---------------------------------------------------------------------------
# 5. Saving and reloading with a temporary JSON file
# ---------------------------------------------------------------------------

def test_save_and_reload_roundtrip(tmp_path):
    file_path = tmp_path / "expenses.json"
    expenses = [
        {"amount": 10.5, "category": "Food", "date": "2026-03-01"},
        {"amount": 25.0, "category": "Transport", "date": "2026-03-02"},
    ]
    main.save_expenses(expenses, file_path)
    assert main.load_expenses(file_path) == expenses


# ---------------------------------------------------------------------------
# 6. Missing JSON file
# ---------------------------------------------------------------------------

def test_missing_file_is_treated_as_empty(tmp_path):
    file_path = tmp_path / "does_not_exist.json"
    assert main.load_expenses(file_path) == []


# ---------------------------------------------------------------------------
# 7. Malformed JSON / bad structure is reported, not destroyed
# ---------------------------------------------------------------------------

def test_malformed_json_raises_and_keeps_file_contents(tmp_path):
    file_path = tmp_path / "expenses.json"
    file_path.write_text("{ not valid json !!!", encoding="utf-8")
    with pytest.raises(main.ExpenseStorageError):
        main.load_expenses(file_path)
    assert file_path.read_text(encoding="utf-8") == "{ not valid json !!!"


def test_non_list_json_raises_and_keeps_file_contents(tmp_path):
    file_path = tmp_path / "expenses.json"
    file_path.write_text(json.dumps({"unexpected": "object"}), encoding="utf-8")
    with pytest.raises(main.ExpenseStorageError):
        main.load_expenses(file_path)
    assert json.loads(file_path.read_text(encoding="utf-8")) == {"unexpected": "object"}


def test_bad_record_structure_raises_and_keeps_file_contents(tmp_path):
    file_path = tmp_path / "expenses.json"
    file_path.write_text(json.dumps([{"cost": 5}]), encoding="utf-8")
    with pytest.raises(main.ExpenseStorageError):
        main.load_expenses(file_path)

@pytest.mark.parametrize("amount", [0, -5, float("nan"), float("inf")])
def test_invalid_stored_amounts_are_rejected(tmp_path, amount):
    file_path = tmp_path / "expenses.json"
    record = {
        "amount": amount,
        "category": "Food",
        "date": "2026-03-15",
    }
    file_path.write_text(json.dumps([record]), encoding="utf-8")

    with pytest.raises(main.ExpenseStorageError):
        main.load_expenses(file_path)

# ---------------------------------------------------------------------------
# 8. Monthly filtering and totals
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_expenses():
    return [
        {"amount": 10.0, "category": "Food", "date": "2026-03-01"},
        {"amount": 20.0, "category": "Food", "date": "2026-03-15"},
        {"amount": 5.0, "category": "Transport", "date": "2026-03-20"},
        {"amount": 99.0, "category": "Food", "date": "2026-04-01"},  # other month
    ]


def test_monthly_filtering_and_totals(sample_expenses):
    summary = main.summarize_month(sample_expenses, "2026-03")
    assert summary["count"] == 3
    assert summary["total"] == 35.0
    assert summary["category_totals"] == {"Food": 30.0, "Transport": 5.0}


# ---------------------------------------------------------------------------
# 9. Category averages with different counts per category
# ---------------------------------------------------------------------------

def test_category_counts_and_averages(sample_expenses):
    summary = main.summarize_month(sample_expenses, "2026-03")
    assert summary["category_counts"] == {"Food": 2, "Transport": 1}
    # Food: 30.0 / 2 = 15.0 ; Transport: 5.0 / 1 = 5.0
    assert summary["category_totals"]["Food"] / summary["category_counts"]["Food"] == 15.0
    assert summary["category_totals"]["Transport"] / summary["category_counts"]["Transport"] == 5.0


# ---------------------------------------------------------------------------
# 10. Month with no expenses
# ---------------------------------------------------------------------------

def test_month_with_no_expenses(sample_expenses):
    summary = main.summarize_month(sample_expenses, "2026-01")
    assert summary["count"] == 0
    assert summary["total"] == 0.0
    assert summary["category_totals"] == {}
    assert summary["category_counts"] == {}


# ---------------------------------------------------------------------------
# Extra: month input validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["2026-13", "2026-00", "13-2026", "2026-3",
                                 "2026/03", "March", ""])
def test_invalid_month_strings_are_rejected(raw):
    with pytest.raises(ValueError):
        main.validate_month(raw)


def test_valid_month_strings_are_accepted():
    assert main.validate_month(" 2026-03 ") == "2026-03"
    assert main.validate_month("2026-12") == "2026-12"