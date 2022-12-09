import os
import logging
from functools import partial

import redis

from dotenv import load_dotenv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, CallbackQueryHandler, \
    CommandHandler, MessageHandler 


logger = logging.getLogger("quizbot")

def start(bot, update):
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2")
        ],
        [
            InlineKeyboardButton("Option 3", callback_data="3"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text='Please choose:',
        reply_markup=reply_markup
    )
    return "ECHO"


def echo(bot, update):
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return "ECHO"


def handle_users_reply(bot, update, redis_db):
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = redis_db.get(chat_id)
    
    states_functions = {
        'START': start,
        'ECHO': echo
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        redis_db.set(chat_id, next_state)
    except Exception as err:
        print(err)


if __name__ == '__main__':
    load_dotenv()
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    redis_db = redis.Redis(
        host=os.getenv("REDIS_DB"),
        port=os.getenv("REDIS_PORT"),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )
    token = os.getenv("TG_BOT_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CallbackQueryHandler(partial(handle_users_reply, redis_db=redis_db))
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            partial(handle_users_reply, redis_db=redis_db)
        )
    )
    dispatcher.add_handler(
        CommandHandler('start', partial(handle_users_reply, redis_db=redis_db))
    )
    updater.start_polling()
    updater.idle()
