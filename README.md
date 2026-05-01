# decorator

## New functionality

Project now supports reading financial transactions not only from JSON, but also
from **CSV** and **XLSX** files (via `pandas`).

Implemented in `src/transactions_io.py`:

- `read_transactions_from_csv(path)` → `list[dict]`
- `read_transactions_from_excel(path)` → `list[dict]`

## Search and categories

Implemented in `src/operations_processing.py`:

- `process_bank_search(data, search)` — search in `description` using `re`
- `process_bank_operations(data, categories)` — count categories using `Counter`

## Console UI

Interactive flow implemented in `src/main.py` (menu, status filter, optional
sorting, RUB-only filter and description search).

## Quick usage

```python
from src.transactions_io import read_transactions_from_csv, read_transactions_from_excel

transactions_csv = read_transactions_from_csv("data/transactions.csv")
transactions_xlsx = read_transactions_from_excel("data/transactions_excel.xlsx")
```

Run console program:

```bash
python -c "from src.main import main; main()"
```

