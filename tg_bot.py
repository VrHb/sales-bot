import os
import logging
from functools import partial

import redis

from dotenv import load_dotenv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, CallbackQueryHandler, \
    CommandHandler, MessageHandler 

from api_interections import get_token, get_products, get_product, get_file, \
    get_cart, create_cart


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


def create_user_cart(user_id):
    token_params = get_token()
    token = f"Bearer {token_params['access_token']}"
    cart = create_cart(token, user_id)
    return cart


def get_product_from_cms(product_id):
    token_params = get_token()
    token = f"Bearer {token_params['access_token']}"
    product_params = get_product(token, product_id)["data"]
    loaded_image_id = product_params["relationships"]["main_image"]["data"]["id"]
    image_link = get_file(token, loaded_image_id)["data"]["link"]["href"]
    return {
        "name": product_params["attributes"]["name"],
        "sku": product_params["attributes"]["sku"],
        "description": product_params["attributes"]["description"],
        "image_link": image_link,
    }


def handle_menu(bot, update):
    product_id = update.callback_query.data
    product = get_product_from_cms(product_id)
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    keyboard = [
        [
            InlineKeyboardButton("1 кг", callback_data=1),
            InlineKeyboardButton("5 кг", callback_data=5),
            InlineKeyboardButton("10 кг", callback_data=10)
        ],
        [
            InlineKeyboardButton("Назад", callback_data="back")
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    bot.send_photo(
        chat_id=chat_id,
        photo=product["image_link"],
        caption=f"*{product['name']}*\n\n{product['description']}",
        parse_mode="markdown",
        reply_markup=reply_markup
    )
    return "HANDLE_DESCRIPTION"


def handle_description(bot, update):
    user_reply = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    logger.info(user_reply)
    # user_cart = create_user_cart(chat_id)
    if user_reply == "back":
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
        chat_id = update.callback_query.message.chat_id
        message_id = update.callback_query.message.message_id
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        bot.send_message(
            chat_id=chat_id,
            text="Choose:",
            reply_markup=reply_markup
        )
        return "HANDLE_MENU"
    return "HANDLE_DESCRIPTION"


def handle_users_reply(bot, update, redis_db):
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == "/start":
        user_state = "START"
    else:
        user_state = redis_db.get(chat_id)

    logger.info(user_state)
    
    states_functions = {
        "START": start,
        "HANDLE_MENU": handle_menu,
        "HANDLE_DESCRIPTION": handle_description,
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
        MessageHandler(
            Filters.text,
            partial(handle_users_reply, redis_db=redis_db)
        )
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(handle_users_reply, redis_db=redis_db)
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            "start", 
            partial(handle_users_reply, redis_db=redis_db)
        )
    )
    updater.start_polling()
    updater.idle()
