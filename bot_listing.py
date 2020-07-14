from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import requests
import urllib3


vkgroup_id = 123  # id сообщества
tkn = 'token_string'  # токен сообщества


# не забудьте создать базу данных
# выводимые кнопки


confirm_button = confirmkeybord = """
{
    "one_time": true,
    "buttons": [
      [{
        "action": {
          "type": "text",
          "payload": "{\\"button\\": \\"1\\"}",
          "label": "ДА"
        },
        "color": "positive"
      },
     {
        "action": {
          "type": "text",
          "payload": "{\\"button\\": \\"2\\"}",
          "label": "НЕТ"
        },
        "color": "negative"
      }]
    ]
  } """

kb = keyboard = """
{
    "one_time": true,
    "buttons": [
      [{
        "action": {
          "type": "text",
          "payload": "{\\"button\\": \\"1\\"}",
          "label": "14-00"
        },
        "color": "default"
      },
     {
        "action": {
          "type": "text",
          "payload": "{\\"button\\": \\"2\\"}",
          "label": "15-00"
        },
        "color": "default"
      }],
      [{
        "action": {
          "type": "text",
          "payload": "{\\"button\\": \\"3\\"}",
          "label": "16-00"
        },
        "color": "default"
      },
     {
        "action": {
          "type": "text",
          "payload": "{\\"button\\": \\"4\\"}",
          "label": "17-00"
        },
        "color": "default"
      }]
    ]
  } """

# Функция для проверки регистрации
def to_reg(usr):
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''select count(*) from RegUsers where userid=%s''' % usr
    cursor.execute(raw)
    output = cursor.fetchone()
    result = int(''.join(str(output[0])))
    return result

# Создание строки для регистрации
def regstart(usr):
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''insert into RegUsers(userid, state) VALUES(%s, 1)''' % usr
    cursor.execute(raw)
    conn.commit()
    conn.close()
    send_message(usr, 'Скажи свое имя, чтобы я смог внести тебя в список охраны.')

# Завершение регистрации
def regfinish(usr):
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''update RegUsers set state = 5 where userid = %s''' %usr
    cursor.execute(raw)
    conn.commit()
    conn.close()


# Состояние регистрации
def getstate(usr):
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''select state from RegUsers where userid=%s''' % usr
    cursor.execute(raw)
    output = cursor.fetchone()
    result = int(''.join(str(output[0])))
    return result


# Записать ФИ
def write_fi(usr, msg):
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''update RegUsers set fi = '%s', state = 2 where userid=%s''' % (msg, usr)
    cursor.execute(raw)
    conn.commit()
    conn.close()
    send_message(usr, 'Также мне нужны твои контакты для связи. Я должен иметь возможность в любой момент связаться с тобой. Номера телефона будет достаточно.')


# Записать АОН
def write_aon(usr, msg):
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''update RegUsers set aon = '%s', state = 3 where userid = %s''' % (msg, usr)
    cursor.execute(raw)
    conn.commit()
    conn.close()
    send_button(usr)


# Записать время
def write_time(usr, msg):
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''update RegUsers set tp_time = '%s', state = 4 where userid=%s''' % (msg, usr)
    cursor.execute(raw)
    conn.commit()
    conn.close()
    # send_message(usr, 'Введите AON')


# Отправка сообщения
def send_message(peer_id, message):
    vk.messages.send(
        peer_id=peer_id, # 187029521
        message=message,
        random_id=get_random_id()
    )


# Отправить кнопки
def send_button(usr):
    vk.messages.send(
        peer_id=usr,  # 187029521
        message='Мне нужно знать точное время отключения питания. Лучше всего это делать во время обходов охраны. Выбери удобное для себя время:',
        random_id=get_random_id(),
        keyboard=kb
    )


def send_confirm_button(usr, msg):
    vk.messages.send(
        peer_id=usr,  # 187029521
        message=msg,
        random_id=get_random_id(),
        keyboard=confirm_button
    )


# Чеклсит
def checklist(usr):
    datalist = []
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''select fi, aon, tp_time from RegUsers where userid = %s''' % usr
    cursor.execute(raw)
    output = cursor.fetchall()
    conn.commit()
    conn.close()
    data = output[0]
    result = '''Давай сверим данные, все верно?
Имя: %s
Телефон: %s
Время: %s
''' % (data[0], data[1], data[2])
    send_confirm_button(usr, result)


# Очистка данных пользователя
def clear_user(usr, msg):
    conn = sqlite3.connect("DB.db")
    cursor = conn.cursor()
    raw = '''delete from RegUsers where userid=%s''' % (usr)
    cursor.execute(raw)
    conn.commit()
    conn.close()
    send_message(usr, msg)


# Подключение
vkBotSession = VkApi(token=tkn)
longPoll = VkBotLongPoll(vkBotSession, vkgroup_id)
vk = vkBotSession.get_api()


# Алгоритм бота
def bot():
    try:
        for event in longPoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                from_id = event.obj['from_id']
                peer_id = event.obj['peer_id']
                message = event.obj['text']
                if 'start' in message.lower():
                    if to_reg(peer_id) == 0:
                        regstart(peer_id)  # kb
                        print(peer_id)
                    else:
                        if getstate(peer_id) == 1:
                            send_message(peer_id, 'Скажи свое имя, чтобы я смог внести тебя в список охраны.')
                        if getstate(peer_id) == 5:
                            send_message(peer_id, 'Вы уже зарегистрированы')
                elif '' != message:
                    if to_reg(peer_id) == 1:
                        if getstate(peer_id) == 1:
                            write_fi(peer_id, message)
                        elif getstate(peer_id) == 2:
                            write_aon(peer_id, message)
                        elif getstate(peer_id) == 3:
                            if message in ['14-00', '15-00', '16-00', '17-00']:
                                write_time(peer_id, message)
                                checklist(peer_id)
                        elif 'ДА' in message:
                            if getstate(peer_id) == 4:
                                regfinish(peer_id)
                                send_message(peer_id, 'Прекрасно! Теперь мы заодно. И помни: все ради общего блага! Наша миссия - спасти человечество.')
                            else:
                                send_message(peer_id, 'shit-shit-fuck-fuck')
                                #clear_user(peer_id, 'Запущена перерегистрация. Введите /reg')
                        elif 'НЕТ' in message:
                            if getstate(peer_id) == 4:
                                clear_user(peer_id, 'Ах, черт, это моя вина. Эти выродки из управления вытянули из меня последние силы. Я все время путаюсь в записях и формулах. Введите start')
                            #else:
                            #   clear_user(peer_id, 'Что-то пошло не так. Запущена перерегистрация. Введите start')
                        elif getstate(peer_id) == 5:
                            send_message(peer_id, 'Вы уже зарегистрированы')
                    else:
                        send_message(peer_id, 'Для регистрации введите start')
    except urllib3.exceptions.ReadTimeoutError:
        bot()


# Запуск бота
bot()


# print(to_reg(1))
