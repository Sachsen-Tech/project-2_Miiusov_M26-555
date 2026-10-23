import re
import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import (
    ALLOWED_TYPES,
    DATA_DIR,
    METADATA_FILE,
    NAME_PATTERN,
)
from primitive_db.core import create_table, delete, drop_table, insert, select, update
from primitive_db.parser import (
    parse_set_clause,
    parse_values,
    parse_where_clause,
    split_where,
)
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Выводит справку по доступным командам базы данных."""

    print("\n***Операции с данными***\n")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец> = <значение> "
        "where <столбец> = <значение> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")

    print("\nУправление таблицами:")
    print("<command> create_table <имя> <столбец:тип> - создать таблицу")
    print("<command> drop_table <имя> - удалить таблицу")
    print("<command> list_tables - показать все таблицы")


def require_table(metadata, table_name):
    """Проверяет существование таблицы и возвращает её структуру."""

    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    return metadata[table_name]


def validate_clause(schema, clause):
    """Проверяет существование столбцов и соответствие типов значений."""

    for column, value in clause.items():
        if column not in schema:
            raise ValueError(f"Столбец '{column}' не существует.")

        if type(value) is not ALLOWED_TYPES[schema[column]]:
            raise ValueError(f"Некорректный тип для столбца '{column}'.")


def print_records(schema, records):
    """Выводит записи базы данных в виде форматированной таблицы."""

    table = PrettyTable()
    table.field_names = list(schema)

    for row in records:
        table.add_row([row[column] for column in schema])

    print(table)


def run():
    """Запускает консольный интерфейс и обрабатывает команды пользователя."""

    print_help()

    while True:
        metadata = load_metadata(METADATA_FILE)
        user_input = prompt.string("\n>>> Введите команду: ").strip()

        if not user_input:
            continue

        command = user_input.split(maxsplit=1)[0].lower()

        try:
            if command == "exit":
                if user_input.lower() != "exit":
                    raise ValueError("Команда exit не принимает аргументы.")

                print("Выход из программы.")
                break

            elif command == "help":
                if user_input.lower() != "help":
                    raise ValueError("Команда help не принимает аргументы.")

                print_help()

            elif command == "create_table":
                args = shlex.split(user_input)

                if len(args) < 3 or not re.fullmatch(NAME_PATTERN, args[1]):
                    raise ValueError("Формат: create_table имя столбец:тип")

                table_name = args[1]
                existed = table_name in metadata

                result = create_table(metadata, table_name, args[2:])

                if result is not None and not existed and table_name in result:
                    save_metadata(METADATA_FILE, result)
                    save_table_data(table_name, [])

            elif command == "drop_table":
                args = shlex.split(user_input)

                if len(args) != 2 or not re.fullmatch(NAME_PATTERN, args[1]):
                    raise ValueError("Формат: drop_table имя_таблицы")

                table_name = args[1]
                existed = table_name in metadata

                result = drop_table(metadata, table_name)

                if result is not None and existed and table_name not in result:
                    save_metadata(METADATA_FILE, result)
                    (DATA_DIR / f"{table_name}.json").unlink(missing_ok=True)

            elif command == "list_tables":
                if user_input.lower() != "list_tables":
                    raise ValueError("Команда list_tables не принимает аргументы.")

                if metadata:
                    print("Список таблиц:")

                    for table_name in metadata:
                        print(f"- {table_name}")
                else:
                    print("Таблиц пока нет.")

            elif command == "insert":
                match = re.fullmatch(
                    rf"insert\s+into\s+({NAME_PATTERN})\s+values\s*\((.*)\)",
                    user_input,
                    re.IGNORECASE | re.DOTALL,
                )

                if match is None:
                    raise ValueError(
                        'Формат: insert into users values ("Sergei", 28, true)'
                    )

                table_name, values_text = match.groups()
                require_table(metadata, table_name)

                values = parse_values(values_text)
                table_data = load_table_data(table_name)

                result = insert(metadata, table_name, values, table_data)

                if result is None:
                    continue

                save_table_data(table_name, result)

                print(
                    f"Запись с ID={result[-1]['ID']} "
                    f'успешно добавлена в таблицу "{table_name}".'
                )

            elif command == "select":
                match = re.fullmatch(
                    rf"select\s+from\s+({NAME_PATTERN})(?:\s+where\s+(.+))?",
                    user_input,
                    re.IGNORECASE | re.DOTALL,
                )

                if match is None:
                    raise ValueError("Формат: select from users [where age = 28]")

                table_name, where_text = match.groups()
                schema = require_table(metadata, table_name)

                where_clause = parse_where_clause(where_text) if where_text else None

                if where_clause is not None:
                    validate_clause(schema, where_clause)

                table_data = load_table_data(table_name)
                records = select(table_data, where_clause)

                if records is not None:
                    print_records(schema, records)

            elif command == "update":
                match = re.fullmatch(
                    rf"update\s+({NAME_PATTERN})\s+set\s+(.+)",
                    user_input,
                    re.IGNORECASE | re.DOTALL,
                )

                if match is None:
                    raise ValueError(
                        'Формат: update users set age = 29 where name = "Sergei"'
                    )

                table_name, conditions_text = match.groups()
                schema = require_table(metadata, table_name)

                set_text, where_text = split_where(conditions_text)
                set_clause = parse_set_clause(set_text)
                where_clause = parse_where_clause(where_text)

                validate_clause(schema, set_clause)
                validate_clause(schema, where_clause)

                table_data = load_table_data(table_name)
                affected = select(table_data, where_clause)

                if affected is None:
                    continue

                if not affected:
                    print("Записи не найдены.")
                    continue

                result = update(table_data, set_clause, where_clause)

                if result is None:
                    continue

                save_table_data(table_name, result)

                for record in affected:
                    print(
                        f"Запись с ID={record['ID']} в таблице "
                        f'"{table_name}" успешно обновлена.'
                    )

            elif command == "delete":
                match = re.fullmatch(
                    rf"delete\s+from\s+({NAME_PATTERN})\s+where\s+(.+)",
                    user_input,
                    re.IGNORECASE | re.DOTALL,
                )

                if match is None:
                    raise ValueError("Формат: delete from users where ID = 1")

                table_name, where_text = match.groups()
                schema = require_table(metadata, table_name)

                where_clause = parse_where_clause(where_text)
                validate_clause(schema, where_clause)

                table_data = load_table_data(table_name)
                affected = select(table_data, where_clause)

                if affected is None:
                    continue

                if not affected:
                    print("Записи не найдены.")
                    continue

                result = delete(table_data, where_clause)

                if result is None:
                    continue

                save_table_data(table_name, result)

                for record in affected:
                    print(
                        f"Запись с ID={record['ID']} успешно удалена "
                        f'из таблицы "{table_name}".'
                    )

            elif command == "info":
                match = re.fullmatch(
                    rf"info\s+({NAME_PATTERN})", user_input, re.IGNORECASE
                )

                if match is None:
                    raise ValueError("Формат: info имя_таблицы")

                table_name = match.group(1)
                schema = require_table(metadata, table_name)
                table_data = load_table_data(table_name)

                print(f"Таблица: {table_name}")

                columns = ", ".join(f"{name}:{kind}" for name, kind in schema.items())

                print(f"Столбцы: {columns}")
                print(f"Количество записей: {len(table_data)}")

            else:
                print(f"Функции '{command}' не существует.")

        except (ValueError, OSError) as error:
            print(f"Ошибка: {error}")
