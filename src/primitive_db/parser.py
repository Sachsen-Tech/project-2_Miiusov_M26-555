import json
import re

ALLOWED_TYPES = (int, str, bool)
_FIELD_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"


def parse_value(text):
    try:
        value = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Некорректное значение. Строки пишите в двойных кавычках, "
            "логические значения — true/false."
        ) from exc

    if type(value) not in ALLOWED_TYPES:
        raise ValueError("Допустимые типы значений: int, str, bool.")

    return value


def parse_values(text):
    try:
        values = json.loads(f"[{text}]")
    except json.JSONDecodeError as exc:
        raise ValueError(
            'Некорректный список значений. Например: ("Sergei", 28, true).'
        ) from exc

    if any(type(value) not in ALLOWED_TYPES for value in values):
        raise ValueError("Допустимые типы значений: int, str, bool.")

    return values


def _parse_assignment(text):
    match = re.fullmatch(
        rf"({_FIELD_PATTERN})\s*=\s*(.+)",
        text.strip(),
        re.DOTALL,
    )

    if match is None:
        raise ValueError("Условие должно иметь вид: столбец = значение.")

    column, raw_value = match.groups()
    return {column: parse_value(raw_value)}


def parse_where_clause(text):
    return _parse_assignment(text)


def parse_set_clause(text):
    return _parse_assignment(text)


def split_where(text):
    """Разделяет SET и WHERE, не затрагивая строки в кавычках."""
    in_quotes = False
    escaped = False

    for i, ch in enumerate(text):
        if escaped:
            escaped = False
            continue

        if in_quotes and ch == "\\":
            escaped = True
            continue

        if ch == '"':
            in_quotes = not in_quotes
            continue

        if not in_quotes and text[i : i + 5].lower() == "where":
            before = text[i - 1] if i else " "
            after = text[i + 5] if i + 5 < len(text) else " "

            if before.isspace() and after.isspace():
                set_part = text[:i].strip()
                where_part = text[i + 5 :].strip()

                if not set_part or not where_part:
                    raise ValueError("Укажите условия после set и where.")

                return set_part, where_part

    raise ValueError("Для update требуется условие where.")
