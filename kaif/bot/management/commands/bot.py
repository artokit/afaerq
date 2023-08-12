import asyncio
import os.path
import random
from asgiref.sync import sync_to_async
from django.core import paginator
from aiogram.dispatcher import FSMContext
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from bot.models import *
from aiogram import executor
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery
from kaif import keyboards
from kaif.settings import dp
from kaif.settings import MEDIA_ROOT
import requests
from kaif import states
from bot.models import TelegramUser
from bot.management.commands import utils


HELLO_TEXT_PATH = os.path.join(os.path.dirname(__file__), 'hello.txt')
START_PHOTO_PATH = os.path.join(os.path.dirname(__file__), 'start.jpg')
INFO_TEXT_PATH = os.path.join(os.path.dirname(__file__), 'info.txt')
RULES_TEXT_PATH = os.path.join(os.path.dirname(__file__), 'rules.txt')
BONUS_TEXT_PATH = os.path.join(os.path.dirname(__file__), 'bonus.txt')
WORK_TEXT_PATH = os.path.join(os.path.dirname(__file__), 'work.txt')
CRYPTO_PAYMENTS = PaymentCrypto.objects.all()
PAYMENTS = [i.title for i in CRYPTO_PAYMENTS]


async def get_user_balance_in_text(user_id):
    user = (await TelegramUser.objects.aget_or_create(user_id=user_id))[0]
    course = get_course(user.balance)
    return f'Ваш баланс:  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC'


def get_course():
    ltc_course = requests.get('https://apirone.com/api/v2/ticker?currency=ltc').json()['rub']
    return ltc_course


def get_course_btc():
    btc_course = requests.get('https://apirone.com/api/v2/ticker?currency=btc').json()['rub']
    return btc_course


@dp.message_handler(Text('< Назад'), state=states.EnterAmount.enter)
@dp.message_handler(commands=['start'], state='*')
async def start(message: Message, state: FSMContext):
    await state.reset_data()
    await state.finish()
    await TelegramUser.objects.aget_or_create(user_id=message.chat.id, username=message.chat.username)

    with open(HELLO_TEXT_PATH, 'rb') as f:
        text = f.read().decode()

    if utils.START_PHOTO:
        await message.answer_photo(
            utils.START_PHOTO,
            caption=text,
            reply_markup=keyboards.get_start()
        )

    else:
        msg = await message.answer_photo(
            open(START_PHOTO_PATH, 'rb'),
            caption=text,
            reply_markup=keyboards.get_start()
        )
        utils.START_PHOTO = msg.photo[-1].file_id


@dp.callback_query_handler(lambda call: call.data == 'info')
async def get_info(call: CallbackQuery):
    with open(INFO_TEXT_PATH, 'rb') as f:
        await call.message.delete()
        await call.message.answer(
            f.read().decode(),
            reply_markup=keyboards.get_start()
        )


@dp.callback_query_handler(lambda call: call.data == 'rules')
async def get_rules(call: CallbackQuery):
    with open(RULES_TEXT_PATH, 'rb') as f:
        await call.message.delete()
        await call.message.answer(
            f.read().decode(),
            reply_markup=keyboards.get_start()
        )


@dp.callback_query_handler(lambda call: call.data == 'bonus')
async def get_bonus(call: CallbackQuery):
    with open(BONUS_TEXT_PATH, 'rb') as f:
        await call.message.delete()
        await call.message.answer(
            f.read().decode().replace('USER_ID', str(call.message.chat.id)),
            reply_markup=keyboards.get_start(),
            parse_mode='markdown'
        )


@dp.callback_query_handler(lambda call: call.data == 'work')
async def get_work(call: CallbackQuery):
    with open(WORK_TEXT_PATH, 'rb') as f:
        await call.message.delete()
        await call.message.answer(
            f.read().decode(),
            reply_markup=keyboards.get_start()
        )


@dp.callback_query_handler(lambda call: call.data == 'profile')
async def get_profile(call: CallbackQuery):
    username_text = f'Логин: {call.message.chat.username}\n' if call.message.chat.username else ''
    surname = f'Фамилия: {call.message.chat.last_name}\n' if call.message.chat.last_name else ''
    # TODO: Рейтинг магазина.
    await call.message.answer(
        '👑 Профиль 👑\n\n'
        f'{username_text}\n'
        f'Имя: {call.message.chat.first_name}\n\n'
        f'{surname}\n'
        'Рейтинг магазина: ⭐️ 4.9/5 (2162 шт.)\n\n'
        'Твой баланс: 0 руб.\n'
        'Покупок: 0\n'
        'Персональная скидка: 0 %\n\n'
        'Приглашены: 0\n'
        'Бонусов получено: 0 руб.\n\n'
        f'Пригласить друга и получить бонус: `https://t.me/GLuv_Bot?start={call.message.chat.id}`',
        reply_markup=keyboards.get_start(),
        parse_mode='markdown'
    )


@dp.callback_query_handler(lambda call: call.data == 'add_balance')
async def add_balance(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer('Выберите способ оплаты для пополнения счета:', reply_markup=keyboards.get_payment_keyboard())


@dp.callback_query_handler(lambda call: call.data == 'to_start')
async def to_start_inline(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await start(call.message, state)


@dp.callback_query_handler(lambda call: call.data.startswith('payment'))
async def get_count_of_money(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    crypto = await PaymentCrypto.objects.aget(title=call.data.replace('payment:', ''))
    await states.EnterAmount.enter.set()
    await state.set_data({'payment_type': crypto})
    await call.message.answer(
        'Отличный выбор! А теперь введи сумму пополнения в Российский рубль.\n  <i>Сумма может быть не менее 300 и не более 300000</i>',
        reply_markup=keyboards.get_back(),
        parse_mode='html'
    )


@dp.message_handler(state=states.EnterAmount.enter)
async def enter_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer(
        'Ошибка ввода. Введите сумму пополнения!',
        reply_markup=keyboards.get_back()
    )

    amount = int(message.text)
    if not (300 < amount < 300000):
        return await message.answer(
        'Необходимо ввести сумму в диапазоне от 300 до 300000!',
        reply_markup=keyboards.get_back()
    )

    await message.answer(
        'Заявка на пополнение **#404933**\n'
        'Способ пополнения: LTC\n'
        f'На баланс: *{amount} руб*.\n\n'
        '👇 👇 👇\n'
        f'Сумма к оплате: `{round(amount/get_course(), 4)}` LTC\n'
        '☝️ ☝️ ☝️\n\n'
        '⚠️⚠️⚠️ Необходимо перевести точную сумму для оплаты! ⚠️⚠️⚠️\n'
        'После подтверждения заявки вы получите реквизиты для оплаты! У вас будет 30 минут для того, что бы оплатить.'
        'Вы можете отправлять сообщения оператору технической поддержки.',
        parse_mode='markdown',
        reply_markup=keyboards.accept(amount)
    )
    await state.finish()


@dp.callback_query_handler(lambda call: call.data.startswith('accept'))
async def accept_deal(call: CallbackQuery):
    await call.message.delete()
    crypto = await PaymentCrypto.objects.aget(title='LTC')
    amount = int(call.data.replace('accept:', ''))
    await call.message.answer(
        'Заявка на пополнение **#404933**\n'
        'Способ пополнения: LTC\n'
        f'На баланс: *{amount} руб*.\n\n'
        '👇 👇 👇\n'
        f'Сумма к оплате: `{round(amount/get_course(), 4)}` LTC\n'
        '☝️ ☝️ ☝️\n\n'
        '⚠️⚠️⚠️ ПЕРЕВОДИТЬ НАДО ТОЧНУЮ СУММУ! ⚠️⚠️⚠️\n\n\n\n'
        f'Реквизиты для оплаты: `{crypto.card}`\n\n'
        '*Время для оплаты - 30 минут.*',
        reply_markup=keyboards.final(),
        parse_mode='markdown'
    )


@dp.callback_query_handler(lambda call: call.data == 'choose_city')
async def choose_city(call: CallbackQuery):
    await call.message.delete()
    cities = [i async for i in City.objects.all()]
    await call.message.answer(
        '***Выбери город:***',
        reply_markup=keyboards.choose_city(cities),
        parse_mode='markdown'
    )


@dp.callback_query_handler(lambda call: call.data.startswith('city'))
async def get_goods(call: CallbackQuery):
    await call.message.delete()
    city = await City.objects.aget(pk=int(call.data.replace('city:', '')))
    goods = [i async for i in Product.objects.filter(city=city, pre_order=False)]
    goods.reverse()

    if not goods:
        return await call.message.answer(
            'Упс, все уже раскупили... Ожидай пополнения',
            reply_markup=keyboards.get_start()
        )

    await call.message.answer(
        'Отличный выбор!\n'
        '***А теперь выбери нужный товар:***',
        reply_markup=await keyboards.get_goods(list(goods)),
        parse_mode='markdown'
    )


@dp.callback_query_handler(lambda call: call.data.startswith('pcity'))
async def get_pre_city(call: CallbackQuery):
    await call.message.delete()
    city = await City.objects.aget(pk=int(call.data.replace('pcity:', '')))
    goods = [i async for i in Product.objects.filter(city=city, pre_order=True)]
    goods.reverse()

    if not goods:
        return await call.message.answer(
            'Упс, все уже раскупили... Ожидай пополнения',
            reply_markup=keyboards.get_start()
        )

    await call.message.answer(
        'Отличный выбор!\n'
        '***А теперь выбери нужный товар:***',
        reply_markup=await keyboards.get_goods(list(goods)),
        parse_mode='markdown'
    )


@dp.callback_query_handler(lambda call: call.data.startswith('product'))
async def choose_pack(call: CallbackQuery):
    product_id, pack_id = map(int, call.data.split(':')[1:])
    await call.message.answer(
        'Отличный выбор!\n***А теперь выбери район:***',
        parse_mode='markdown',
        reply_markup=await keyboards.get_areas(product_id, pack_id)
    )


@dp.callback_query_handler(lambda call: call.data.startswith('area'))
async def get_full_product(call: CallbackQuery):
    product_pk, pack_pk, area_pk = map(int, call.data.split(':')[1:])
    product = await Product.objects.aget(pk=product_pk)
    user = await TelegramUser.objects.aget(user_id=call.message.chat.id)
    pack = await Pack.objects.aget(pk=pack_pk)
    area = await Area.objects.aget(pk=area_pk)
    desc = product.description if product.description else ''
    pr = Product.objects.select_related('city')
    city = (await pr.aget(pk=product_pk)).city

    if product.photo:
        return await call.message.answer_photo(
            open(os.path.join(MEDIA_ROOT, str(product.photo)), 'rb'),
            f'***{product.name} {pack.weight} г *** _({city.name}, {area.name})_\n\n'
            f'_{desc}_\n\n'
            f'Цена: {pack.price} руб.\n\n'
            'У вас нет персональной скидки! Покупайте в магазине и получайте скидку для постоянных клиентов\n\n'
            f'***Твой баланс: {user.balance} руб. ({round(user.balance/get_course(), 6)} BTC)***',
            parse_mode='markdown',
            reply_markup=keyboards.get_buy(pack.price, pre_order=product.pre_order)
        )

    await call.message.answer(
        f'***{product.name} {pack.weight} г. *** *({city.name}, {area.name})*\n\n'
        f'*{desc}*\n\n'
        f'Цена: {pack.price} руб.\n\n'
        'У вас нет персональной скидки! Покупайте в магазине и получайте скидку для постоянных клиентов\n\n'
        f'***Твой баланс: {user.balance} руб. ({round(user.balance/get_course(), 6)} BTC)***',
        parse_mode='markdown',
        reply_markup=keyboards.get_buy(pack.price, pre_order=product.pre_order)
    )


@dp.callback_query_handler(lambda call: call.data.startswith('buy'))
async def go_to_buy(call: CallbackQuery):
    price = int(call.data.split(':')[1])
    await call.message.answer(
        f'У вас недостаточно баланса! Выберите способ пополнения счета на сумму {price} руб.:',
        reply_markup=keyboards.get_inline_add_balance(price)
    )


@dp.callback_query_handler(lambda call: call.data.startswith('request_to_pay'))
async def inline_pay(call: CallbackQuery):
    amount = int(call.data.replace('request_to_pay:', ''))
    await call.message.answer(
        'Заявка на пополнение **#404933**\n'
        'Способ пополнения: LTC\n'
        f'На баланс: *{amount} руб*.\n\n'
        '👇 👇 👇\n'
        f'Сумма к оплате: `{round(amount/get_course(), 4)}` LTC\n'
        '☝️ ☝️ ☝️\n\n'
        '⚠️⚠️⚠️ Необходимо перевести точную сумму для оплаты! ⚠️⚠️⚠️\n'
        'После подтверждения заявки вы получите реквизиты для оплаты! У вас будет 30 минут для того, что бы оплатить.'
        'Вы можете отправлять сообщения оператору технической поддержки.',
        parse_mode='markdown',
        reply_markup=keyboards.accept(amount)
    )


@dp.callback_query_handler(lambda call: call.data == 'pre_order')
async def get_pre_order(call: CallbackQuery):
    await call.message.delete()
    cities = [i async for i in City.objects.all()]
    await call.message.answer(
        '***Выбери город:***',
        reply_markup=keyboards.choose_city(cities, prefix=True),
        parse_mode='markdown'
    )


@dp.callback_query_handler(lambda call: call.data.startswith('comments'))
async def get_comment(call: CallbackQuery):
    page_number = int(call.data.replace('comments:', ''))
    comment, comments = await get_comment_by_page(page_number)

    if call.message.caption:
        await call.message.delete()
        await call.message.answer(
            'Рейтинг магазина: ⭐️ ***4,8/5 (2113 шт.)***\n\n'
            '***Ваши отзывы делают наш магазин лучше!***\n\n'
            f'{"⭐️"*comment.count_star}\n'
            f'_{comment.content}_\n'
            f'{comment.date}\n\n\n'
            f'***Отзывы можно оставлять только к совершенным покупкам.***',
            parse_mode='markdown',
            reply_markup=keyboards.get_comment_paginator(page_number, comments)
        )
    else:
        await call.message.edit_text(
            'Рейтинг магазина: ⭐️ <b>4,8/5 (2113 шт.)</b>\n\n'
            '<b>Ваши отзывы делают наш магазин лучше!</b>\n\n'
            f'{"⭐️" * comment.count_star}\n'
            f'<i>{comment.content}</i>\n'
            f'{comment.date}\n\n\n'
            f'<b>Отзывы можно оставлять только к совершенным покупкам.</b>',
            parse_mode='html',
            reply_markup=keyboards.get_comment_paginator(page_number, comments)
        )


@dp.callback_query_handler(lambda call: call.data == 'list_goods')
async def get_list_goods(call: CallbackQuery):
    text = ''
    number = 0

    async for city in City.objects.all():
        products = [i async for i in Product.objects.filter(city=city)]
        if products:
            text += f'Доступные товары "{city.name}"\n'
        for product in products:
            async for pack in product.packs.all():
                number += 1
                text += f'<b>{number}) {product.name}, {pack.weight} г - {pack.price} руб.</b>\n'
                async for area in pack.areas.all():
                    text += f'<i>{area.name}</i>\n'
                text += '\n'

    await call.message.answer(
        text,
        reply_markup=keyboards.get_start(),
        parse_mode='html'
    )


@sync_to_async
def get_comment_by_page(page_number):
    comments = Comment.objects.all()
    p = Paginator(comments, 1)
    comment = p.page(page_number).object_list[0]
    return comment, len(comments)

#
# @dp.message_handler(Text('Пополнить баланс'))
# async def get_balance(message: Message):
#     user = (await TelegramUser.objects.aget_or_create(user_id=message.chat.id, username=message.chat.username))[0]
#     course = get_course(user.balance)
#
#     await states.EnterAmount.enter.set()
#     await message.answer(
#         f'Ваш баланс:  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC\n'
#         'Введите сумму для пополнения в RUB. Минимум для пополнения - 100 RUB',
#         reply_markup=keyboards.balance
#     )
#
#
# @dp.message_handler(state=states.EnterAmount.enter)
# async def enter_amount(message: Message, state: FSMContext):
#     if message.text.isdigit():
#         amount = int(message.text)
#         if amount < 100:
#             return await message.answer('Введите сумму для пополнения в RUB. Минимум для пополнения - 100 RUB')
#         user = await TelegramUser.objects.aget(user_id=message.chat.id)
#         course = get_course(user.balance)
#
#         await states.EnterAmount.select_payment.set()
#         await state.set_data({'amount': amount})
#
#         return await message.answer(
#             f'<b>Ваш баланс:</b>  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC\n\n\n\n'
#             f'<b>Выберите способ оплаты:</b>',
#             parse_mode='html',
#             reply_markup=keyboards.payments_keyboard
#         )
#
#     await message.answer('Введите сумму для пополнения в RUB. Минимум для пополнения - 100 RUB')
#
#
# @dp.message_handler(Text('Инъекции'), state='*')
# async def injection(message: Message, state: FSMContext):
#     await state.reset_data()
#     await state.finish()
#     await message.answer('https://telegra.ph/Vnutrivennyj-priem-narkotikov-05-15-2', reply_markup=keyboards.injection)
#
#
# @dp.message_handler(Text('Помощь'), state='*')
# async def get_help(message: Message, state: FSMContext):
#     await state.reset_data()
#     await state.finish()
#     await message.answer('@Tigr_lip', reply_markup=keyboards.assistance)
#
#
# @dp.message_handler(commands='otzivi', state='*')
# async def get_comments(message: Message, state=FSMContext):
#     await states.GetComments.next_comments.set()
#     num_page = (await state.get_data()).get('page', 1)
#
#     try:
#         page = await get_comments_page(num_page)
#     except paginator.EmptyPage:
#         await state.set_data({'page': 1})
#         return await get_comments(message, state)
#
#     text = ''
#
#     async for com in page:
#         text += f'➖➖От {com.nickname} {com.date}➖➖\n' \
#                f'{com.content}\n\n'
#
#     await state.update_data({'page': num_page + 1})
#     await message.answer(
#         'Показать еще (нажмите 👉 /otzivi)\n\n' + text,
#         reply_markup=keyboards.injection
#     )
#
#
# @sync_to_async
# def get_comments_page(num_page):
#     comments = paginator.Paginator(Comment.objects.all(), 5)
#     return comments.page(num_page).object_list
#
#
# @dp.message_handler(Text('Совершить покупку'), state='*')
# async def buy_product(message: Message):
#     user = await TelegramUser.objects.aget(user_id=message.chat.id)
#     course = get_course(user.balance)
#
#     await states.BuyProduct.select_city.set()
#
#     await message.answer(
#         f'<b>Ваш баланс:</b>  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC\n\n'
#         '<b>Для покупки нажмите на свой город внизу:</b>',
#         parse_mode='html',
#         reply_markup=await keyboards.keyboard_builder(City.objects.all(), 'name')
#     )
#
#
# @dp.message_handler(lambda message: message.text in PAYMENTS, state=states.EnterAmount.select_payment)
# async def select_payment(message: Message, state: FSMContext):
#     amount = (await state.get_data())['amount']
#     title = message.text
#     obj = await PaymentCrypto.objects.aget(title=title)
#     after_buy = (await state.get_data()).get('buy', False)
#
#     await state.update_data({'payment': obj})
#     if obj:
#         r = requests.get(f'https://apirone.com/api/v2/ticker?currency={obj.code}').json()['rub']
#         st = f'{await get_user_balance_in_text(message.chat.id)}\n\n' if not after_buy else ''
#         middle = '<b>Как баланс пополнится - переходите к покупкам.</b>\n' if not after_buy else ''
#         await message.answer(
#             st +
#             f'<b>Переведите {obj.code.upper()}</b>\n' +
#             middle +
#             '➖➖➖➖➖➖➖➖➖➖\n'
#             f'<b>Кошелек:</b> {obj.card}\n'
#             f'<b>Сумма:</b> {round(amount/r, 8)} {obj.code.upper()}\n'
#             f'<b>Курс:</b> {int(r)} RUB/{obj.code.upper()}\n'
#             '➖➖➖➖➖➖➖➖➖➖\n'
#             '<b>ЧТОБЫ ОПЛАТА БЫСТРЕЕ ЗАЧИСЛИЛАСЬ, СТАВЬТЕ ВЫСОКУЮ КОМИССИЮ</b>\n\n'
#             f'Чтобы получить кошелек отдельным сообщением нажмите 👉 /my{obj.code.lower()}',
#             parse_mode='html',
#             reply_markup=keyboards.buy if not after_buy else keyboards.after_select_keyboard
#         )
#
#     else:
#         await message.answer(
#             'Неправильный выбор, попробуйте еще раз.\n'
#             'Для выбора варианта нажмите на кнопку снизу'
#         )
#
#
# @dp.message_handler(Text('💰Проверить оплату💰'), state=states.EnterAmount.select_payment)
# async def check_pay(message: Message, state: FSMContext):
#     await asyncio.sleep(random.randint(5, 10))
#     amount = (await state.get_data())['amount']
#     obj = (await state.get_data())['payment']
#     if obj:
#         r = requests.get(f'https://apirone.com/api/v2/ticker?currency={obj.code}').json()['rub']
#
#         user = await TelegramUser.objects.aget(user_id=message.chat.id)
#         course = get_course(user.balance)
#
#         await message.answer(
#             f'<b>Ваш баланс:</b>  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC\n\n'
#             f'<b>Переведите {obj.code.upper()}</b>\n'
#             '<b>Как баланс пополнится - переходите к покупкам.</b>\n'
#             '➖➖➖➖➖➖➖➖➖➖\n'
#             f'<b>Кошелек:</b> {obj.card}\n'
#             f'<b>Сумма:</b> {round(amount/r, 8)} {obj.code.upper()}\n'
#             f'<b>Курс:</b> {int(r)} RUB/{obj.code.upper()}\n'
#             '➖➖➖➖➖➖➖➖➖➖\n'
#             '<b>ЧТОБЫ ОПЛАТА БЫСТРЕЕ ЗАЧИСЛИЛАСЬ, СТАВЬТЕ ВЫСОКУЮ КОМИССИЮ</b>\n\n'
#             f'Чтобы получить кошелек отдельным сообщением нажмите 👉 /my{obj.code.lower()}',
#             parse_mode='html',
#             reply_markup=keyboards.buy
#         )
#
#     else:
#         await message.answer(
#             'Неправильный выбор, попробуйте еще раз.\n'
#             'Для выбора варианта нажмите на кнопку снизу'
#         )
#
#
# @dp.message_handler(state=states.BuyProduct.select_city)
# async def select_city(message: Message, state: FSMContext):
#     try:
#         city = await City.objects.aget(name=message.text)
#     except City.DoesNotExist:
#         return await message.answer(
#             'Неправильный выбор, попробуйте еще раз.\n'
#             'Для выбора варианта нажмите на кнопку снизу',
#             reply_markup=await keyboards.keyboard_builder(City.objects.all(), 'name')
#         )
#
#     await state.update_data({'city': city})
#     await states.BuyProduct.select_product.set()
#
#     await message.answer(
#         f'{await get_user_balance_in_text(message.chat.id)}\n\n'
#         f'<b>Вы выбрали</b> "{city.name}"\n\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         f'🏡 <b>Город:</b> {city.name}\n'
#         '➖➖➖➖➖➖➖➖➖➖\n\n'
#         '<b>Выберите товар:</b>',
#         parse_mode='html',
#         reply_markup=await keyboards.keyboard_builder(Product.objects.filter(city=city), 'name')
#     )
#
#
# @dp.message_handler(state=states.BuyProduct.select_product)
# async def select_product(message: Message, state: FSMContext):
#     user_data = await state.get_data()
#     city = user_data['city']
#     try:
#         product = await Product.objects.aget(name=message.text, city=city)
#     except Product.DoesNotExist:
#         return await message.answer(
#             'Неправильный выбор, попробуйте еще раз.\n'
#             'Для выбора варианта нажмите на кнопку снизу',
#             reply_markup=await keyboards.keyboard_builder(Product.objects.filter(city=city), 'name')
#         )
#
#     await state.update_data({'product': product})
#     await states.BuyProduct.select_count.set()
#     await state.get_data()
#
#     await message.answer(
#         f'{await get_user_balance_in_text(message.chat.id)}\n\n'
#         f'<b>Вы выбрали</b> "{product.name}". \n\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         f'<b>🏡 Город</b>: {city.name}\n'
#         f'<b>📦 Товар</b>: {product.name}\n'
#         '➖➖➖➖➖➖➖➖➖➖\n\n'
#         '<b>Выберите фасовку</b>:',
#         reply_markup=await keyboards.keyboard_builder(product.packs.all(), '__str__'),
#         parse_mode='html'
#     )
#
#
# @dp.message_handler(state=states.BuyProduct.select_count)
# async def select_weight(message: Message, state: FSMContext):
#     user_data = await state.get_data()
#     city = user_data['city']
#     product = user_data['product']
#
#     if message.text not in [str(i) async for i in product.packs.all()]:
#         return await message.answer(
#             'Неправильный выбор, попробуйте еще раз.\n'
#             'Для выбора варианта нажмите на кнопку снизу',
#             reply_markup=await keyboards.keyboard_builder(Product.objects.filter(city=city), 'name')
#         )
#
#     pack_index = [str(i) async for i in product.packs.all()].index(message.text)
#     pack = [i async for i in product.packs.all()][pack_index]
#     await state.update_data({'pack': pack})
#     await states.BuyProduct.select_area.set()
#
#     await message.answer(
#         f'{await get_user_balance_in_text(message.chat.id)}\n\n'
#         f'<b>Вы выбрали</b> "{str(pack)}". \n\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         f'<b>🏡 Город</b>: {city.name}\n'
#         f'<b>📦 Товар</b>: {product.name}\n'
#         f'<b>📋 Фасовка:</b> {str(pack).replace("руб", "рублей")}\n'
#         '➖➖➖➖➖➖➖➖➖➖\n\n'
#         '<b>Выберите район</b>:',
#         reply_markup=await keyboards.keyboard_builder(pack.areas.all(), 'name'),
#         parse_mode='html',
#     )
#
#
# @dp.message_handler(state=states.BuyProduct.select_area)
# async def select_area(message: Message, state: FSMContext):
#     user_data = await state.get_data()
#     city = user_data['city']
#     product = user_data['product']
#     pack = user_data['pack']
#
#     if message.text not in [i.name async for i in pack.areas.all()]:
#         return await message.answer(
#             'Неправильный выбор, попробуйте еще раз.\n'
#             'Для выбора варианта нажмите на кнопку снизу',
#             reply_markup=await keyboards.keyboard_builder(Product.objects.filter(city=city), 'name')
#         )
#     area_index = [i.name async for i in pack.areas.all()].index(message.text)
#     area = [i async for i in pack.areas.all()][area_index]
#     await state.update_data({'pack': area})
#
#     await states.EnterAmount.select_payment.set()
#     await state.set_data({'amount': pack.price, 'buy': True})
#
#     await message.answer(
#         f'<b>Вы выбрали </b>"{area.name}".\n\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         f'<b>🏡 Город:</b> {city.name}\n'
#         f'<b>📦 Товар:</b> {product.name}\n'
#         f'<b>📋 Район:</b> {area.name}\n'
#         f'<b>📋 Фасовка:</b> {str(pack).replace("руб", "рублей")}\n'
#         '➖➖➖➖➖➖➖➖➖➖\n\n'
#         '<b>Выберите способ оплаты:</b>',
#         parse_mode='html',
#         reply_markup=keyboards.payments_keyboard
#     )
#
#
# @dp.message_handler(commands=['mybtc', 'myltc'])
# async def get_address(message: Message):
#     code = message.text.replace('/my', '')
#     await message.answer(
#         (await PaymentCrypto.objects.aget(code=code)).card
#     )
#
#
# @dp.message_handler(Text('Прайс'))
# async def get_price_list(message: Message):
#     await states.BuyProduct.select_city.set()
#     await message.answer(
#         'Сейчас в наличии:\n\n'
#         f'{await get_text_for_price_list()}'
#         f'{await get_user_balance_in_text(message.chat.id)}\n\n'
#         f'<b>Для покупки нажмите на свой город внизу:</b>',
#         parse_mode='html',
#         reply_markup=await keyboards.keyboard_builder(City.objects.all(), 'name')
#     )
#
#
# @dp.message_handler(Text('Visa/MasterCard'), state=states.EnterAmount.select_payment)
# async def select_exchange(message: Message, state: FSMContext):
#     amount = (await state.get_data()).get('amount')
#     await states.ExchangeCard.exchange_select.set()
#
#     await message.answer(
#         f'{await get_user_balance_in_text(message.chat.id)}\n\n'
#         f'В результате обмена Вы получите BTC\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         'ВАЖНО! Оплата идентифицируется по стоимости. Диапазон колебания цены 1-50 рублей.\n'
#         'Сумма оплаты указанная для каждого из обменников ПРИБЛИЗИТЕЛЬНАЯ.\n'
#         'Точную сумму Вы получите вместе с реквизитами на оплату.\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         f'Сумма пополнения : {amount} RUB.\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         '<b>Выберите обменный пункт</b>\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         f'{await get_select_exchange_text(amount)}',
#         parse_mode='html',
#         reply_markup=await keyboards.keyboard_builder(Exchange.objects.all(), 'name')
#     )
#
#
# @dp.message_handler(state=states.ExchangeCard.exchange_select)
# async def exchange_pay(message: Message, state: FSMContext, obj=None):
#     amount = (await state.get_data()).get('amount')
#     if not obj:
#         try:
#             obj = await Exchange.objects.aget(name=message.text)
#         except Exchange.DoesNotExist:
#             return await select_exchange(message, state)
#
#     await state.update_data({'exc': obj})
#
#     await asyncio.sleep(random.randint(10, 15))
#     await states.ExchangeCard.check_payment.set()
#     await message.answer(
#         f'{await get_user_balance_in_text(message.chat.id)}\n\n'
#         'В результате обмена Вы получите BTC\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         f'<b>Вы выбрали обменный пункт {obj.name}\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         f'✅ Номер вашей заявки: {random.randint(12332479, 12882679)}\n'
#         f'✅ Номер карты: {obj.card}\n'
#         f'✅ Сумма для пополнения: {amount} RUB\n'
#         '➖➖➖➖➖➖➖➖➖➖\n'
#         '✅ ВЫДАННЫЕ РЕКВИЗИТЫ ДЕЙСТВУЮТ 30 МИНУТ\n'
#         '✅ ВЫ ПОТЕРЯЕТЕ ДЕНЬГИ, ЕСЛИ ОПЛАТИТЕ ПОЗЖЕ\n'
#         '✅ ПЕРЕВОДИТЕ ТОЧНУЮ СУММУ. НЕВЕРНАЯ СУММА НЕ БУДЕТ ЗАЧИСЛЕНА.\n'
#         '✅ ОПЛАТА ДОЛЖНА ПРОХОДИТЬ ОДНИМ ПЛАТЕЖОМ.\n'
#         '✅ ПРОБЛЕМЫ С ОПЛАТОЙ? ПИСАТЬ В TELEGRAM : babushkahelpbot\n'
#         '✅ С ПРОБЛЕМНОЙ ЗАЯВКОЙ ОБРАЩАЙТЕСЬ НЕ ПОЗДНЕЕ 24 ЧАСОВ С МОМЕНТА ОПЛАТЫ.</b>',
#         reply_markup=keyboards.check_exchange,
#         parse_mode='html'
#     )
#
#
# @dp.message_handler(Text('Проверить оплату'), state=states.ExchangeCard.check_payment)
# async def check_exc(message: Message, state: FSMContext):
#     await asyncio.sleep(random.randint(10, 15))
#     await exchange_pay(message, state, (await state.get_data())['exc'])
#
#
# @dp.message_handler(Text('Отменить оплату'), state=states.ExchangeCard.check_payment)
# async def cancel_exc(message: Message, state: FSMContext):
#     await state.reset_data()
#     await start(message, state)
#
#
# @sync_to_async
# def get_text_for_price_list():
#     text = ''
#     for city in City.objects.all():
#         text += f'➖➖➖<b>{city.name.upper()}</b>➖➖➖\n\n'
#         for product in Product.objects.filter(city=city):
#             pack_text = "\n".join([str(i) for i in product.packs.all()])
#             text += f'<b>{product.name}</b>\n' \
#                     f'{pack_text}\n\n'
#     return text
#
#
# @sync_to_async
# def get_select_exchange_text(amount):
#     text = ''
#
#     for exc in Exchange.objects.all():
#         text += f'<b>{exc.name}</b>\nСумма к оплате ПРИМЕРНО: {round(amount*((100+exc.percent)/100), 2)} RUB\n\n'
#
#     return text
#

class Command(BaseCommand):
    help = 'not help'

    def handle(self, *args, **options):
        executor.Executor(dp).start_polling()
