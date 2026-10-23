import shlex

import prompt

from primitive_db.core import create_table, drop_table
from primitive_db.utils import load_metadata, save_metadata


def print_help():
    print("\n***База данных***")
    print("Функции:")
    print("<command> create_table <имя> <столбец:тип> ... - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя> - удалить таблицу")
    print("<command> help - справочная информация")
    print("<command> exit - выход из программы\n")


def run():
    filepath = "db_meta.json"

    print_help()

    while True:
        metadata = load_metadata(filepath)

        user_input = prompt.string("Введите команду: ")

        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Ошибка: некорректный формат команды.")
            continue

        if not args:
            continue

        command = args[0]

        if command == "exit":
            if len(args) != 1:
                print("Ошибка: команда exit не принимает аргументы.")
                continue
            print("Выход из программы.")
            break

        elif command == "help":
            print_help()

        elif command == "list_tables":
            if len(args) != 1:
                print("Ошибка: команда list_tables не принимает аргументы.")
                continue

            if metadata:
                print("Список таблиц:")
                for table_name in metadata:
                    print(f"- {table_name}")
            else:
                print("Таблиц пока нет.")

        elif command == "create_table":
            if len(args) < 3:
                print("Ошибка: укажите имя таблицы и столбцы.")
                continue

            table_name = args[1]
            columns = args[2:]

            existed = table_name in metadata

            metadata = create_table(metadata, table_name, columns)

            if not existed and table_name in metadata:
                save_metadata(filepath, metadata)

        elif command == "drop_table":
            if len(args) != 2:
                print("Ошибка: укажите имя таблицы.")
                continue

            table_name = args[1]

            existed = table_name in metadata

            metadata = drop_table(metadata, table_name)

            if existed and table_name not in metadata:
                save_metadata(filepath, metadata)

        else:
            print(f"Функции '{command}' нет. Попробуйте снова.")
