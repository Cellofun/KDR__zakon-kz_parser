import csv

import time as t

from datetime import datetime

import requests
from requests.exceptions import ConnectionError, Timeout, ProxyError

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


# Получить список всех статей
def get_news_list():
    # Список прокси
    proxies = {
        'https': 'http://135.181.152.128:3128',
        'http': 'http://135.181.152.128:3128'
    }

    # Повторный запрос данных при выбрасывании исключений
    error = ''
    for i in range(3):
        try:
            # Получение данных страницы новостей
            news_page = requests.get('https://www.zakon.kz/news', proxies=proxies)
        except (ConnectionError, Timeout, ProxyError) as e:
            error = e
            print(error)
            t.sleep(10)
            continue
        else:
            break
    else:
        raise Exception(error)

    soup = BeautifulSoup(news_page.content, 'html.parser')

    # Выбор массивов статей
    news_list = soup.find_all('div', class_='cat_news_item')

    # Возвращение список статей без массива с текущей датой
    return news_list[1:]


# Получить данные статьи
def get_news_data(article):
    # Настройка прокси
    proxy = '135.181.152.128:3128'
    webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
        "httpProxy": proxy,
        "ftpProxy": proxy,
        "sslProxy": proxy,
        "proxyType": "MANUAL",

    }

    # Инициализация драйвера Selenium для загрузки комментариев
    driver = webdriver.Firefox()

    # Повторный запрос данных при выбрасывании исключений
    error = ''
    for i in range(3):
        try:
            # Получение данных страницы статьи
            article_url = article.a.get('href')
            driver.get('https://www.zakon.kz/news' + article_url)
        except (TimeoutException, WebDriverException) as e:
            error = e
            print(error)
            t.sleep(10)
            continue
        else:
            break
    else:
        raise Exception(error)

    # Скролл до конца страницы для загрузки виджета с комментариями
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Нажатие на кнопку "Показать комментарии" для загрузки комментариев
    try:
        wait = WebDriverWait(driver, 100)  # Время ожидания сильно увелично, так как прокси очень нешустрый :(
        comments_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'togglecomm')))
        comments_button.click()
    except TimeoutException:
        print('No comments added')

    # Получение данных статьи
    article_page = driver.page_source
    soup = BeautifulSoup(article_page, 'html.parser')

    # Закрытие драйвера
    driver.quit()

    # Получение данных из выбранной статьи
    try:
        article_data = soup.find('div', class_='feeditem')
        title = article_data.find('div', class_='fullhead').h1.text
        date = article_data.find('div', class_='newsdate').span.text
        content = article_data.find('div', class_='newscont').text
    except AttributeError:
        raise Exception('Could not fetch article')

    try:
        comment_count = article_data.find('span', class_='zknc-total-count').text
        # Получение списка комментариев при их наличии
        comments = []
        if article_data.find('div', class_='zknc-message'):
            for comment in article_data.find_all('div', class_='zknc-message'):
                comments.append([comment.get_text()])
    except AttributeError:
        comment_count = None
        comments = None

    return [title, date, content.strip(), comment_count, comments]


# Создание файла с данными всех статей
def write_file(news_list):
    # Создание csv-файла
    with open('zakon.kz %s.csv' % datetime.now(), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Date', 'Content', 'Comments count', 'Comments'])
        # Запись данных статей
        for news in news_list:
            writer.writerow(get_news_data(news))


if __name__ == '__main__':
    write_file(get_news_list())
