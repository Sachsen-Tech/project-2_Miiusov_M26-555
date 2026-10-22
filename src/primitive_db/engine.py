import prompt


def welcome():
    print("Первая попытка запустить проект!")

    while True:
        print("\n***")
        print("<command> exit - выйти из программы")
        print("<command> help - справочная информация")

        command = prompt.string("Введите команду: ")

        if command == "exit":
            break
        elif command == "help":
            continue
