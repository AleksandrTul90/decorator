"""Console entry point for the banking transactions project."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.operations_processing import process_bank_search
from src.transactions_loaders import load_transactions

STATUSES = ("EXECUTED", "CANCELED", "PENDING")


def _normalize_yes(value: str) -> bool:
    return value.strip().lower() in {"да", "yes", "y", "true", "1"}


def _get_status_from_user(input_fn=input, print_fn=print) -> str:
    while True:
        print_fn(
            "Программа: Введите статус, по которому необходимо выполнить фильтрацию.\n"
            "Доступные для фильтровки статусы: EXECUTED, CANCELED, PENDING"
        )
        status = input_fn("Пользователь: ").strip()
        upper = status.upper()
        if upper in STATUSES:
            print_fn(f'Программа: Операции отфильтрованы по статусу "{upper}"')
            return upper
        print_fn(f'Программа: Статус операции "{status}" недоступен.')


def _parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _filter_by_status(data: list[dict[str, Any]], status: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for op in data:
        op_status = op.get("status")
        if isinstance(op_status, str) and op_status.upper() == status:
            result.append(op)
    return result


def _filter_rub_only(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for op in data:
        currency = None
        amount = op.get("amount")
        if isinstance(amount, dict):
            currency = amount.get("currency")
            if isinstance(currency, dict):
                currency = currency.get("name")
        if isinstance(currency, str) and currency.upper() in {"RUB", "RUR"}:
            result.append(op)
    return result


def _sort_by_date(data: list[dict[str, Any]], ascending: bool) -> list[dict[str, Any]]:
    return sorted(
        data,
        key=lambda op: _parse_date(op.get("date")) or datetime.min,
        reverse=not ascending,
    )


def _format_operation(op: dict[str, Any]) -> str:
    date_raw = op.get("date")
    dt = _parse_date(date_raw)
    date_str = dt.strftime("%d.%m.%Y") if dt else str(date_raw or "")

    description_raw = op.get("description")
    description = description_raw if isinstance(description_raw, str) else ""

    amount = op.get("amount")
    amount_value = ""
    amount_currency = ""
    if isinstance(amount, dict):
        val = amount.get("amount")
        cur = amount.get("currency")
        if isinstance(val, (int, float, str)):
            amount_value = str(val)
        if isinstance(cur, dict):
            cur_name = cur.get("name")
            if isinstance(cur_name, str):
                amount_currency = cur_name

    return f"{date_str} {description}\nСумма: {amount_value} {amount_currency}".rstrip()


def main(input_fn=input, print_fn=print) -> None:
    """Run interactive console program."""
    print_fn(
        "Программа: Привет! Добро пожаловать в программу работы \n"
        "с банковскими транзакциями.\n"
        "Выберите необходимый пункт меню:\n"
        "1. Получить информацию о транзакциях из JSON-файла\n"
        "2. Получить информацию о транзакциях из CSV-файла\n"
        "3. Получить информацию о транзакциях из XLSX-файла"
    )

    choice = input_fn("Пользователь: ").strip()
    if choice == "1":
        source = "json"
        print_fn("Программа: Для обработки выбран JSON-файл.")
    elif choice == "2":
        source = "csv"
        print_fn("Программа: Для обработки выбран CSV-файл.")
    elif choice == "3":
        source = "xlsx"
        print_fn("Программа: Для обработки выбран XLSX-файл.")
    else:
        print_fn("Программа: Некорректный пункт меню.")
        return

    path = input_fn("Пользователь: Введите путь к файлу: ").strip()
    try:
        transactions = load_transactions(source, path)
    except Exception as e:  # noqa: BLE001
        print_fn(f"Программа: Ошибка чтения файла: {e}")
        return

    status = _get_status_from_user(input_fn=input_fn, print_fn=print_fn)
    filtered = _filter_by_status(transactions, status)

    print_fn("Программа: Отсортировать операции по дате? Да/Нет")
    if _normalize_yes(input_fn("Пользователь: ")):
        print_fn("Программа: Отсортировать по возрастанию или по убыванию?")
        order = input_fn("Пользователь: ").strip().lower()
        ascending = "возрастан" in order
        filtered = _sort_by_date(filtered, ascending=ascending)

    print_fn("Программа: Выводить только рублевые транзакции? Да/Нет")
    if _normalize_yes(input_fn("Пользователь: ")):
        filtered = _filter_rub_only(filtered)

    print_fn(
        "Программа: Отфильтровать список транзакций по определенному слову \n"
        "в описании? Да/Нет"
    )
    if _normalize_yes(input_fn("Пользователь: ")):
        search = input_fn("Пользователь: Введите строку поиска: ").strip()
        filtered = process_bank_search(filtered, search)

    if not filtered:
        print_fn(
            "Программа: Не найдено ни одной транзакции, подходящей под ваши\n"
            "условия фильтрации"
        )
        return

    print_fn("Программа: Распечатываю итоговый список транзакций...")
    print_fn("Программа:")
    print_fn(f"Всего банковских операций в выборке: {len(filtered)}\n")
    for op in filtered:
        print_fn(_format_operation(op))
        print_fn("")
