import datetime
import logging
import os
import random
import sqlite3
import sys
import time
import requests
import schedule
from conf import bot_token, db_path, start_times
from handlers.db import get_sendto, mess_reset, get_admins_list


def send_photo(file_path, caption, send_to):
    with open(file_path, 'rb') as img_file:
        img = {'photo': ('_', img_file, 'image/jpeg')}
        url = f'https://api.telegram.org/bot{bot_token}/sendPhoto?chat_id={send_to}&caption={caption}'
        response = requests.post(url, files=img)
        return response.text


def send_text(message_text, send_to):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    response = requests.post(url, json={'chat_id': send_to, 'parse_mode': 'html', 'text': message_text})
    return response.text


def send_random_message():
    channel_id = get_sendto()[0]
    conn = sqlite3.connect(db_path())
    c = conn.cursor()
    c.execute('SELECT * FROM messages WHERE last_send is NULL')
    messages_db = c.fetchall()
    if len(messages_db) < 1:  # min count not send in db
        admins = get_admins_list()
        mess_text = mess_reset()
        for admin in admins:
            send_text(mess_text, admin[0])
    c.execute('SELECT * FROM messages WHERE last_send is NULL')
    messages_db = c.fetchall()
    message_db = messages_db[random.randint(0, len(messages_db) - 1)]
    message_id, text, last_sent = message_db
    img_mess = open_random_image(message_id)
    if img_mess:
        send_photo(file_path=os.path.join(os.getcwd(), img_mess), caption=text, send_to=channel_id)
    else:
        send_text(text, send_to=channel_id)
    c.execute('UPDATE messages SET last_send=? WHERE ids=?',
              (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), message_id))
    conn.commit()
    conn.close()


def open_random_image(message_id):
    img_files = []
    source_dir = 'img/'
    for path, dirs, files in os.walk(source_dir):
        for filename in files:
            fullpath = os.path.join(path, filename)
            try:
                if int(filename.split('_')[0]) == message_id:
                    img_files.append(fullpath)
                else:
                    if len(img_files) >= 1:
                        break
                    continue
            except ValueError:
                continue
    if len(img_files) != 0:
        img = img_files[random.randrange(0, len(img_files))]
        return img
    else:
        return False


def main_run():
    print(f'Task will sending : {start_times}')
    for times in start_times:
        schedule.every().day.at(times).do(send_random_message)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    main_run()
