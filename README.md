# Wikilinks


### Описание
Проект предназначен для поиска пути между двумя заданными ссылками Википедии (на данный момент только русский сегмент). </br>
Глубина поиска переменная, по дефолту равна 3. Логи по просмотренным страницам можно найти в 'entry_log.txt'.

####
#### *Input*: 
- ссылка, с которой начинается поиск (по дефолту: https://ru.wikipedia.org/wiki/Xbox_360_S 
- ссылка, которую нужно найти (по дефолту: https://ru.wikipedia.org/wiki/Nintendo_3DS)
- глубина поиска (дефолтная задаётся в settings в параметре MAX_DEPTH, равна 3)
#### *Output*: 
- ссылки, по которым можно дойти от первой до второй, с предложениями, в которых они были найдены

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
###### _Python 3.9.5_
