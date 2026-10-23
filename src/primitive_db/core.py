
def create_table(metadata, table_name, columns):
    if table_name in metadata:
        print(f"Ошибка: Таблица '{table_name}' уже существует.")
        return metadata

    if not columns:
        print("Ошибка: Необходимо указать столбцы.")
        return metadata

    allowed_types = ["int", "str", "bool"]
    table_columns = {"ID": "int"}

    for column in columns:
        if column.count(":") != 1:
            print(f"Ошибка: Некорректный столбец '{column}'.")
            return metadata

        column_name, column_type = column.split(":")

        if not column_name:
            print("Ошибка: Имя столбца не может быть пустым.")
            return metadata

        if column_type not in allowed_types:
            print(f"Ошибка: Некорректный тип '{column_type}'.")
            return metadata

        if column_name == "ID" and column_type == "int":
            continue

        if column_name in table_columns:
            print(f"Ошибка: Столбец '{column_name}' уже существует.")
            return metadata

        table_columns[column_name] = column_type

    metadata[table_name] = table_columns

    print(f"Таблица '{table_name}' успешно создана.")
    return metadata


def drop_table(metadata, table_name):
    if table_name not in metadata:
        print(f"Ошибка: Таблица '{table_name}' не существует.")
        return metadata

    del metadata[table_name]

    print(f"Таблица '{table_name}' успешно удалена.")
    return metadata
