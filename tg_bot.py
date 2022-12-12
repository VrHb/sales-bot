import os
import logging
from functools import partial

import redis

from dotenv import load_dotenv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, CallbackQueryHandler, \
    CommandHandler, MessageHandler 

from api_interections import get_token, get_products, get_product, get_file


logger = logging.getLogger("quizbot")

def start(bot, update):
    token_params = get_token()
    token = f"Bearer {token_params['access_token']}"
    products = get_products(token)["data"]
    keyboard = []
    for product in products:
        keyboard.append(
            [InlineKeyboardButton(
                product["attributes"]["name"],
                callback_data=product["id"]
            )]
        )
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Choose:",
        reply_markup=reply_markup
    )
    return "HANDLE_MENU"


def echo(bot, update):
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return "ECHO"


def handle_menu(bot, update, redis_db):
    product_id = update.callback_query.data
    token_params = get_token()
    token = f"Bearer {token_params['access_token']}"
    logger.info(product_id)
    product_params = get_product(token, product_id)["data"]
    product_name = product_params["attributes"]["name"]
    product_description = product_params["attributes"]["description"]
    loaded_image_id = product_params["relationships"]["main_image"]["data"]["id"]
    image_link = get_file(token, loaded_image_id)["data"]["link"]["href"]
    chat_id = update.callback_query.message.chat_id
    state = redis_db.get(chat_id)
    logger.info(state)
    message_id = update.callback_query.message.message_id
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    bot.send_photo(
        chat_id=chat_id,
        photo=image_link,
        caption=f"*{product_name}*\n\n{product_description}",
        parse_mode="markdown"
    )
    return "START"


def handle_users_reply(bot, update, redis_db):
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_state = "HANDLE_MENU"
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == "/start":
        user_state = "START"
    else:
        user_state = redis_db.get(chat_id)
    
    states_functions = {
        "START": start,
        "HANDLE_MENU": handle_menu,
        "ECHO": echo
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        redis_db.set(chat_id, next_state)
    except Exception as err:
        print(err)


if __name__ == "__main__":
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
    bot_token = os.getenv("TG_BOT_TOKEN")
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CallbackQueryHandler(partial(handle_menu, redis_db=redis_db))
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            partial(handle_users_reply, redis_db=redis_db)
        )
    )
    dispatcher.add_handler(
        CommandHandler("start", partial(handle_users_reply, redis_db=redis_db))
    )
    updater.start_polling()
    updater.idle()
