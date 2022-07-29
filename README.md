1. Описание
    Проект парсинга позволяет следить за актуальностью версии Python, а так же скачивать и анализировать полученную информацию.
2. Запуск
    Создать и активировать виртуальное окружение
        - python -m venv venv
        - source venv/scripts/activate
    Установить зависимости
        - pytho -m pip install --upgrade pip
        - pip install -r requirement.txt
3. Режимы работы и команды
    Команды:
        Ссылки на новости Python и новые версии.
            python src/main.py whats-new -с
        Скачать документацию последней версии Python в PDF.
            python src/main.py download
        Ссылки на документацию всех версий Python в табличном виде.
            python src/main.py latest-versions -o pretty
        Получитьстатусы и количество PEP с записью в файл формата csv.
            python src/main.py pep -o file
4. Технические данные
    Python, BeautifulSoup4
    (-o file) сохраняется в папке src/results/
    Скачанная документация - src/downloads/
    Логи работы парсера - src/logs
5. Автор
    Будник Сергей Александрович
    Python-разработчик (Backend)
    Россия, г. Краснодар
    E-mail: bazzz@list.ru
    Telegram: @Bercut38
