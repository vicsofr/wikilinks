# Wikilinks


### Описание
Проект предназначен для поиска пути между двумя заданными ссылками Википедии (на данный момент только русский сегмент). </br>
Глубина поиска не больше трёх. Логи по просмотренным страницам можно найти в entry_log.txt 

####
- *input*: две ссылки: начала и конца поиска </br>(по дефолту первая: https://ru.wikipedia.org/wiki/Xbox_360_S и вторая: https://ru.wikipedia.org/wiki/Nintendo_3DS)
- *output*: ссылки, по которым можно дойти от первой до второй, с предложением, в котором ссылка была найдена

### Создание окружения
```shell script
python -m venv venv
```
- *или любое другое*

### Активация окружения
```shell script
source venv/bin/activate
```

### Установка зависимостей
```shell script
pip install -r requirements.txt
```

### Запуск проекта
```shell script
python wikilinks.py
```