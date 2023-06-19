import telebot
from telebot import types
from geopy.geocoders import Nominatim
import requests

# Конфигурационные параметры
TELEGRAM_TOKEN = 'You_TOKEN'
BITRIX24_API_ENDPOINT = 'https://YOUR_BITRIX24_DOMAIN/rest/YOUR_USER_ID/YOUR_API_KEY/'

# Инициализация Telegram бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Инициализация геокодера
geolocator = Nominatim(user_agent='my_bot')

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    accept_button = types.InlineKeyboardButton("Принять в работу", callback_data='accept')
    reject_button = types.InlineKeyboardButton("Отклонить", callback_data='reject')
    keyboard.add(accept_button, reject_button)
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=keyboard)

# Обработка нажатий кнопок
@bot.callback_query_handler(func=lambda call: True)
def button_callback(call):
    if call.data == 'accept':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        arrival_button = types.InlineKeyboardButton("Выезд на объект", callback_data='arrival')
        keyboard.add(arrival_button)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Подтвердите выезд на объект:', reply_markup=keyboard)
    elif call.data == 'reject':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        reasons = ['Причина 1', 'Причина 2', 'Причина 3']
        for reason in reasons:
            button = types.InlineKeyboardButton(reason, callback_data='reason_' + reason)
            keyboard.add(button)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Выберите причину отклонения:', reply_markup=keyboard)
    elif call.data == 'arrival':
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        location_button = types.KeyboardButton("Отправить местоположение", request_location=True)
        keyboard.add(location_button)
        bot.send_message(call.message.chat.id, 'Отправьте ваше текущее местоположение:', reply_markup=keyboard)

# Обработка получения геолокации
@bot.message_handler(func=lambda message: message.location is not None)
def handle_location(message):
    latitude = message.location.latitude
    longitude = message.location.longitude
    address = get_address_from_coordinates(latitude, longitude)
    send_to_bitrix24('Принято в работу', '', 'Да', address)
    bot.send_message(message.chat.id, 'Подрядчик прибыл на объект по адресу:\n{}'.format(address))

# Получение адреса по координатам
def get_address_from_coordinates(latitude, longitude):
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    if location:
        return location.address
    else:
        return 'Не удалось определить адрес'

# Отправка сообщения в Bitrix24
def send_to_bitrix24(status, rejection_reason, site_visit, location):
    data = {
        'fields': {
            'TITLE': 'Telegram заявка',
            'NAME': 'Telegram бот',
            'STATUS': status,
            'REJECTION_REASON': rejection_reason,
            'SITE_VISIT': site_visit,
            'LOCATION': location
        }
    }
    response = requests.post(BITRIX24_API_ENDPOINT + 'crm.lead.add', json=data)
    # Здесь вы можете добавить обработку ответа от Bitrix24

# Запуск бота
bot.polling()
