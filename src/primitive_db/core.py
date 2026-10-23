import re

from primitive_db.utils import load_table_data

from primitive_db.decorators import handle_db_errors, confirm_action, log_time, create_cacher

ALLOWED_TYPES = {"int": int, "str": str, "bool": bool}
NAME_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"


@handle_db_errors
def create_table(metadata, table_name, columns):

    if not re.fullmatch(NAME_PATTERN, table_name):
        raise ValueError("Некорректное имя таблицы.")

    if table_name in metadata:
        raise ValueError(f"Таблица '{table_name}' уже существует.")

    if not columns:
        raise ValueError("Необходимо указать хотя бы один столбец.")

    table_columns = {"ID": "int"}

    for column in columns:
        if column.count(":") != 1:
            raise ValueError(f"Некорректное описание столбца '{column}'.")

        column_name, column_type = column.split(":")

        if not re.fullmatch(NAME_PATTERN, column_name):
            raise ValueError(f"Некорректное имя столбца '{column_name}'.")

        if column_type not in ALLOWED_TYPES:
            raise ValueError(f"Некорректный тип данных '{column_type}'.")

        if column_name == "ID":
            if column_type != "int":
                raise ValueError("Столбец ID должен иметь тип int.")
            continue

        if column_name in table_columns:
            raise ValueError(f"Столбец '{column_name}' уже существует.")

        table_columns[column_name] = column_type

    metadata[table_name] = table_columns
    print(f"Таблица '{table_name}' успешно создана.")
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):

    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    del metadata[table_name]
    print(f"Таблица '{table_name}' успешно удалена.")
    return metadata


@handle_db_errors
@log_time
def insert(metadata, table_name, values, table_data=None):

    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    columns = [
        (name, column_type)
        for name, column_type in metadata[table_name].items()
        if name != "ID"
    ]

    if len(values) != len(columns):
        raise ValueError("Количество значений не соответствует количеству столбцов.")

    for (name, column_type), value in zip(columns, values):
        if type(value) is not ALLOWED_TYPES[column_type]:
            raise ValueError(f"Некорректный тип значения для столбца '{name}'.")

    if table_data is None:
        table_data = load_table_data(table_name)

    new_id = max((record["ID"] for record in table_data), default=0) + 1
    new_record = {"ID": new_id}

    for (name, _), value in zip(columns, values):
        new_record[name] = value

    table_data.append(new_record)
    return table_data


def _matches(record, where_clause):

    if where_clause is None:
        return True

    return all(
        key in record
        and type(record[key]) is type(value)
        and record[key] == value
        for key, value in where_clause.items()
    )


_select_cache = create_cacher()
@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    key = (repr(table_data), repr(where_clause))

    indexes = _select_cache(
        key,
        lambda: [
            index
            for index, record in enumerate(table_data)
            if _matches(record, where_clause)
        ],
    )

    return [table_data[index] for index in indexes]


@handle_db_errors
def update(table_data, set_clause, where_clause):

    if not where_clause:
        raise ValueError("Для обновления требуется условие where.")

    if not set_clause:
        raise ValueError("Для обновления требуется условие set.")

    if "ID" in set_clause:
        raise ValueError("Изменять ID запрещено.")

    matched = select(table_data, where_clause)


    for record in matched:
        for column, value in set_clause.items():
            if column not in record:
                raise ValueError(f"Столбец '{column}' не существует.")
            if type(record[column]) is not type(value):
                raise ValueError(f"Некорректный тип значения для '{column}'.")

    for record in matched:
        record.update(set_clause)

    return table_data


@handle_db_errors
@confirm_action("удаление записи")
def delete(table_data, where_clause):

    if not where_clause:
        raise ValueError("Для удаления требуется условие where.")

    return [record for record in table_data if not _matches(record, where_clause)]