from pyrogram import Client
import time

client = Client('anon', api_hash='f18c3490495d98e223f1a7b881140f63', api_id=27139411)
client.start()
client.send_message('GLuv_Bot', '/start')
time.sleep(1)
message = [i for i in client.get_chat_history('GLuv_Bot')][0]

try:
    Client.request_callback_answer(
        client,
        chat_id='GLuv_Bot',
        message_id=message.id,
        callback_data='MAIN_REVIEWS_CALLBACK',
        timeout=1
    )
except TimeoutError:
    print('Похуй')

while True:
    time.sleep(2)
    message = [i for i in client.get_chat_history('GLuv_Bot', -1, -1)][0]
    msg = message.text.split('\n\n', maxsplit=2)[2].replace(
        '\n\n\nОтзывы можно оставлять только к совершенным покупкам.', '')
    count_stars = msg.split('\n')[0].count('⭐')
    date = msg[::-1].split('\n')[0][::-1]
    comment = msg.replace(msg.split('\n')[0], '').replace(date, '').strip()
    print(count_stars, date, comment)
    if Comment.objects.filter(count_star=count_stars, date=date, content=comment):
        print('Такое уже есть')
    else:
        c = Comment(count_star=count_stars, date=date, content=comment)
        c.save()
    try:
        Client.request_callback_answer(
            client,
            chat_id='GLuv_Bot',
            message_id=message.id,
            callback_data=message.reply_markup.inline_keyboard[0][1].callback_data,
            timeout=1
        )
    except TimeoutError:
        pass
