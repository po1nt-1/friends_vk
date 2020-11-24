import inspect
import os
import sys
import time
import webbrowser
from pprint import pprint

import browser_cookie3
import pymongo
import requests
from pymongo import MongoClient
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

client = MongoClient()
db = client["db"]
collection = db["farpost"]


def get_script_dir(follow_symlinks: bool = True) -> str:
    # https://clck.ru/P8NUA
    if getattr(sys, 'frozen', False):  # type: ignore
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


def get_config():
    with open(os.path.join(get_script_dir(), 'config'), 'r',
              encoding="utf-8") as f:
        return f.read().split('\n')


def authorize(client_id):
    url = f'https://oauth.vk.com/authorize?client_id={client_id}' + \
        '&display=page&redirect_uri=https://oauth.vk.com/blank.html' + \
        '&scope=140488159&response_type=token&v=5.124'

    gecko_path = os.path.join(get_script_dir(), 'geckos', 'geckodriver_lin')

    try:
        cj = browser_cookie3.firefox(domain_name='vk.com')
    except AttributeError:
        cj = browser_cookie3.chrome(domain_name='vk.com')
    cj = requests.utils.dict_from_cookiejar(cj)

    response = requests.get('https://vk.com')
    cookies = requests.utils.add_dict_to_cookiejar(
        cj=response.cookies, cookie_dict=cj)
    cookies = requests.utils.dict_from_cookiejar(cookies)

    options = Options()
    options.headless = True
    with Firefox(options=options, service_log_path=None, executable_path=gecko_path) as driver:
        driver.get('https://vk.com')
        for key, value in cookies.items():
            driver.add_cookie({'name': key, 'value': value})
        dr_cooks = driver.get_cookies()
        for dr_cook in dr_cooks:
            driver.add_cookie(dr_cook)
        driver.get(url)
        driver.find_element_by_css_selector(
            'button.flat_button:nth-child(1)').click()

        data = driver.current_url
        if 'access_token' not in data:
            return None

    result = {}
    for elem in ''.join(data.split('#')[1:]).split('&'):
        elem = elem.split('=')
        if elem[0] == 'expires_in':
            continue
        result.update({elem[0]: elem[1]})

    return result


def friends_get(user_id, token):
    if user_id is None:
        return None, None
    url_1 = f'https://api.vk.com/method/users.get?user_ids={user_id}&lang=ru&fields=friend&access_token={token}&v=5.124'
    url_2 = f'https://api.vk.com/method/friends.get?user_id={user_id}&lang=ru&fields=city&access_token={token}&v=5.124'

    response = tuple(requests.get(url_1).json()['response'][0].values())
    print(response)
    if isinstance(response, dict):
        city = response[-1]['title']
    else:
        city = None
    user = (response[1], response[0], response[2], city)

    response = requests.get(url_2).json()
    print(response)
    friends = []
    if 'error' in response:
        friends = None
    else:
        for elem in response['response']['items']:
            print('1', end='')
            if elem.get('city') is not None:
                city = elem.get('city')['title']
            else:
                city = None
            temp = (elem.get('first_name'), elem.get('last_name'),
                    str(elem.get('id')), city)
            friends.append(temp)

    human = {'user_id': user[0], 'first_name': user[1],
             'last_name': user[2], 'city': user[3],
             'friends': friends}
    return user, friends


def main():
    if os.name == "posix":
        pass    # TODO: сделать путь до geckodriver, чтобы потом py2exe
    elif os.name == "nt":
        pass
    else:
        print("Unsupported operating system")
        return None

    app_id, token = get_config()
    secrets = authorize(app_id)

    print(secrets)

    # data = []
    # human = friends_get('200411727', token)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("ConnectionError")


# 200411727 # 278858059 # 280738939
