# Перевод README простыми словами

## Что это?

Это проект для LangJam.

Нужно создать: - свой язык программирования (.cl); - интерпретатор этого
языка; - TCP-чат, логика которого написана на этом языке.

Интерпретатор написан на Python и использует только стандартную
библиотеку.

## Запуск

``` bash
python3 main.py examples/chat.cl 9000
python3 client.py 127.0.0.1 9000
```

или

``` bash
nc 127.0.0.1 9000
```

Команды: - /history - /users - /quit

## Структура проекта

-   lexer.py --- разбивает код на токены.
-   parser.py --- строит AST.
-   interpreter.py --- выполняет AST.
-   runtime.py --- хранит пользователей, историю и встроенные функции.
-   server.py --- TCP-сервер.
-   client.py --- тестовый клиент.
-   examples/chat.cl --- программа на собственном языке.

## Возможности языка

-   переменные;
-   if/else;
-   while;
-   функции;
-   списки;
-   словари;
-   обработчики событий:
    -   on connect(...)
    -   on message(...)
    -   on disconnect(...)

## Встроенные функции

broadcast(), send(), history(), users(), disconnect() и другие.

## Архитектура

chat.cl → Lexer → Parser → AST → Interpreter → Runtime → TCP Server

## Ограничения MVP

Нет сохранения истории, комнат, авторизации, /kick и try/catch.


