import pytest

from src.masks import get_mask_account, get_mask_card_number
from src.processing import filter_by_state, sort_by_date
from src.widget import get_date, mask_account_card


def test_get_mask_account_last4():
    assert get_mask_account("73654108430135874305") == "**4305"


def test_get_mask_card_number_format():
    assert get_mask_card_number("7000792289606361") == "7000 79** **** 6361"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("Visa Platinum 7000792289606361", "Visa Platinum 7000 79** **** 6361"),
        ("MasterCard 5555444433332222", "MasterCard 5555 44** **** 2222"),
        ("Счет 73654108430135874305", "Счет **4305"),
        ("Account 73654108430135874305", "Account **4305"),
        ("", ""),
        ("Без цифр", "Без цифр"),
    ],
)
def test_mask_account_card(value, expected):
    assert mask_account_card(value) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2018-07-11T02:26:18.671407", "11.07.2018"),
        ("2018-07-11", "11.07.2018"),
        ("2018-07-11T02:26:18Z", "11.07.2018"),
        ("", ""),
        ("not-a-date", ""),
        (" ", ""),
    ],
)
def test_get_date_parsing(raw, expected):
    assert get_date(raw) == expected


def test_filter_by_state_default_executed(sample_transactions):
    out = filter_by_state(sample_transactions)
    assert all(op["state"] == "EXECUTED" for op in out)


def test_filter_by_state_canceled(sample_transactions):
    out = filter_by_state(sample_transactions, "CANCELED")
    assert [op["id"] for op in out] == [594226727]


def test_sort_by_date_desc(sample_transactions):
    out = sort_by_date(sample_transactions)
    assert [op["id"] for op in out][:2] == [142264268, 873106923]


def test_sort_by_date_asc(sample_transactions):
    out = sort_by_date(sample_transactions, reverse=False)
    assert [op["id"] for op in out][:2] == [939719570, 895315941]
