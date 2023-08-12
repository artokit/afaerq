from aiogram.types import *
from bot.models import City, Product, Pack


def get_start():
    start = InlineKeyboardMarkup()
    start.add(
        InlineKeyboardButton('Ташкент', callback_data='choose_city'),
        InlineKeyboardButton('💰 Пополнить счет', callback_data='add_balance')
    )
    start.add(
        InlineKeyboardButton('🔜📦ПРЕДЗАКАЗ', callback_data='pre_order')
    )
    start.add(
        InlineKeyboardButton('👑Профиль', callback_data='profile'),
        InlineKeyboardButton('🎁Бонусы', callback_data='bonus')
    )

    start.add(
        InlineKeyboardButton('📃 Правила', callback_data='rules'),
        InlineKeyboardButton('🧾 Поддержка', url='https://t.me/Rezerv_clan_420')
    )
    start.add(
        InlineKeyboardButton('🛒 ВИТРИНА', callback_data='list_goods'),
        InlineKeyboardButton('ℹ️ Информация', callback_data='info')
    )
    start.add(InlineKeyboardButton('НАШ КАНАЛ', url='https://t.me/+CXALWM14qRsxZDky'))
    start.add(InlineKeyboardButton('⭐️ Отзывы 4.9 ⭐️ (2147)', callback_data='comments:1'))
    return start


def get_payment_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('LTC', callback_data='payment:LTC'))
    keyboard.add(InlineKeyboardButton('< Назад', callback_data='to_start'))
    return keyboard


def get_back():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('< Назад'))
    return keyboard


def accept(amount):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('👌 Подтвердить', callback_data=f'accept:{amount}'))
    keyboard.add(InlineKeyboardButton('🚫Отменить', callback_data='to_start'))
    return keyboard


def final():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('👍 Оплачено!', callback_data='check_status'))
    keyboard.add(InlineKeyboardButton('🚫Отменить', callback_data='to_start'))
    return keyboard


def choose_city(cities: list[City], prefix: bool = False):
    keyboard = InlineKeyboardMarkup()
    prefix = 'p' if prefix else ''

    for city in cities:
        keyboard.add(InlineKeyboardButton(city.name, callback_data=f'{prefix}city:{city.pk}'))

    keyboard.add(InlineKeyboardButton('< Назад', callback_data='to_start'))
    return keyboard


async def get_goods(goods: list[Product]):
    keyboard = InlineKeyboardMarkup()

    for product in goods:
        async for pack in product.packs.all():
            keyboard.add(
                InlineKeyboardButton(
                    f'{product.name}, {pack.weight} г',
                    callback_data=f'product:{product.pk}:{pack.pk}'
                )
            )

    keyboard.add(InlineKeyboardButton('< Назад', callback_data='choose_city'))
    return keyboard


async def get_areas(product_pk, pack_pk):
    keyboard = InlineKeyboardMarkup()
    areas = (await Pack.objects.aget(pk=pack_pk)).areas

    async for area in areas.all():
        keyboard.add(InlineKeyboardButton(area.name, callback_data=f'area:{product_pk}:{pack_pk}:{area.pk}'))

    keyboard.add(InlineKeyboardButton('< Назад', callback_data='choose_city'))
    return keyboard


def get_buy(price, pre_order=False):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Купить! камень' if not pre_order else "ЗАКАЗАТЬ", callback_data=f'buy:{price}'))
    keyboard.add(InlineKeyboardButton('< Назад', callback_data='choose_city'))
    return keyboard


def get_inline_add_balance(price):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('LTC', callback_data=f'request_to_pay:{price}'))
    keyboard.add(InlineKeyboardButton('< Назад', callback_data='choose_city'))
    return keyboard


def get_comment_paginator(page_number, max_count):
    keyboard = InlineKeyboardMarkup()
    prev_page = max_count if page_number == 1 else page_number - 1
    next_page = 1 if max_count == page_number else page_number + 1
    keyboard.add(
        InlineKeyboardButton('<--', callback_data=f'comments:{prev_page}'),
        InlineKeyboardButton('-->', callback_data=f'comments:{next_page}')
    )
    keyboard.add(InlineKeyboardButton('< Назад', callback_data='to_start'))
    return keyboard
