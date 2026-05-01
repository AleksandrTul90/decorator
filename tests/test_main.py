from __future__ import annotations

from unittest.mock import patch

from src.main import main


def test_main_happy_path_json_status_and_prints_count() -> None:
    fake_data = [
        {
            "date": "2019-12-08T22:46:21.935582",
            "status": "EXECUTED",
            "description": "Открытие вклада",
            "amount": {"amount": "40542", "currency": {"name": "RUB"}},
        },
        {
            "date": "2019-11-12T17:41:13.342610",
            "status": "CANCELED",
            "description": "Перевод с карты на карту",
            "amount": {"amount": "130", "currency": {"name": "USD"}},
        },
    ]

    # Menu 1 (json), path, status, sort? no, rub only? yes, description filter? no
    inputs = iter(
        [
            "1",
            "data/operations.json",
            "EXECUTED",
            "нет",
            "да",
            "нет",
        ]
    )
    output: list[str] = []

    with patch("src.main.load_transactions", return_value=fake_data):
        main(input_fn=lambda _: next(inputs), print_fn=output.append)

    joined = "\n".join(output)
    assert "Для обработки выбран JSON-файл" in joined
    assert "Операции отфильтрованы по статусу" in joined
    assert "Всего банковских операций в выборке: 1" in joined
    assert "Открытие вклада" in joined


def test_main_wrong_status_then_correct_status() -> None:
    fake_data = [{"status": "EXECUTED", "description": "x", "amount": {}}]

    inputs = iter(
        [
            "1",
            "data/operations.json",
            "test",
            "executed",
            "нет",
            "нет",
            "нет",
        ]
    )
    output: list[str] = []

    with patch("src.main.load_transactions", return_value=fake_data):
        main(input_fn=lambda _: next(inputs), print_fn=output.append)

    joined = "\n".join(output)
    assert 'Статус операции "test" недоступен' in joined
    assert 'Операции отфильтрованы по статусу "EXECUTED"' in joined


def test_main_invalid_menu_choice() -> None:
    inputs = iter(["9"])
    output: list[str] = []

    main(input_fn=lambda _: next(inputs), print_fn=output.append)

    assert "Некорректный пункт меню" in "\n".join(output)
