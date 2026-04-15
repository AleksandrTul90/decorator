# Декоратор `log`

В проекте реализован декоратор `log`, который логирует выполнение функций:

- **Куда пишем логи**:
  - если задан `filename`, логи пишутся в файл (добавлением в конец);
  - если `filename` не задан, логи выводятся в консоль (`print`).
- **Что логируем**:
  - при успехе: время, имя функции, аргументы/kwargs, результат;
  - при ошибке: время, имя функции, тип ошибки, аргументы/kwargs (ошибка пробрасывается дальше).

## Пример

```python
from decorators import log


@log()
def add(a: int, b: int) -> int:
    return a + b


@log(filename="app.log")
def div(a: int, b: int) -> float:
    return a / b
```

## Запуск тестов

```bash
pytest
```

## Покрытие (HTML)

```bash
pytest --cov=decorators --cov-report=html
```

После запуска появится папка `htmlcov/` с HTML-отчётом.

