import os
import time
from textwrap import dedent
import logging
from functools import partial

from dotenv import load_dotenv

import redis

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, CallbackQueryHandler, \
    CommandHandler, MessageHandler 

from api_interections import add_product_to_cart, get_token, get_products, \
    get_product, get_file, get_cart_items, get_cart, create_cart, \
    delete_item_from_cart, create_customer


logger = logging.getLogger("sailbot")

def send_products(bot, chat_id, message_id, token_params):
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
    keyboard.append([InlineKeyboardButton("Корзина", callback_data="cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=chat_id,
        text="Choose:",
        reply_markup=reply_markup
    )
    bot.delete_message(chat_id=chat_id, message_id=message_id)


def send_cart(bot, chat_id, message_id, token_params):
    token = f"Bearer {token_params['access_token']}"
    cart_params = ""
    items = get_cart_items(token, str(chat_id))["data"]
    keyboard = []
    for item in items:
        item_price = item['meta']['display_price']['with_tax']['unit']['formatted']
        item_price_value = item['meta']['display_price']['with_tax']['value']['formatted']
        cart_params += dedent(
        f"""\
        {item['name']}
        {item['description']}
        {item_price} per kg
        {item['quantity']} kg in cart for {item_price_value}

        """
        )
        keyboard.append(
            [InlineKeyboardButton(
                f"Убрать из корзины {item['name']}",
                callback_data=item["id"]
            )]
        )
    keyboard.append([InlineKeyboardButton("Оплатить", callback_data="pay")])
    keyboard.append([InlineKeyboardButton(f"В меню", callback_data="back")])
    total_price = get_cart(token, chat_id)["data"]["meta"]["display_price"]["with_tax"]["formatted"]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=chat_id,
        text=cart_params + f"Total: {total_price}",
        reply_markup=reply_markup,
    )
    bot.delete_message(chat_id=chat_id, message_id=message_id)


def send_description(bot, chat_id, message_id, product_id, token_params):
    keyboard = [
        [InlineKeyboardButton("1 кг", callback_data=f"1 {product_id}"),
            InlineKeyboardButton("5 кг", callback_data=f"5 {product_id}"),
            InlineKeyboardButton("10 кг", callback_data=f"10 {product_id}")
        ],
        [InlineKeyboardButton("Назад", callback_data="back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    product = get_product_from_cms(product_id, token_params)
    bot.send_photo(
        chat_id=chat_id,
        photo=product["image_link"],
        caption=dedent(
            f"""\
            *{product['name']}*

            {product['description']}"""
        ),
        parse_mode="markdown",
        reply_markup=reply_markup
    )
    bot.delete_message(chat_id=chat_id, message_id=message_id)


def start(bot, update, token_params):
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    send_products(bot, chat_id, message_id, token_params)
    return "HANDLE_MENU"


def get_product_from_cms(product_id, token_params):
    token = f"Bearer {token_params['access_token']}"
    product_params = get_product(token, product_id)["data"]
    loaded_image_id = product_params["relationships"]["main_image"]["data"]["id"]
    image_link = get_file(token, loaded_image_id)["data"]["link"]["href"]
    return {
        "id": product_params["id"],
        "name": product_params["attributes"]["name"],
        "sku": product_params["attributes"]["sku"],
        "description": product_params["attributes"]["description"],
        "image_link": image_link,
    }


def handle_menu(bot, update, token_params):
    user_reply = update.callback_query.data
    message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat_id
    if user_reply == "cart":
        send_cart(bot, chat_id, message_id, token_params)
        return "HANDLE_CART"
    product_id = update.callback_query.data
    send_description(bot, chat_id, message_id, product_id, token_params)
    return "HANDLE_DESCRIPTION"


def handle_description(bot, update, token_params):
    token = f"Bearer {token_params['access_token']}"
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    user_reply = update.callback_query.data
    if user_reply == "back":
        send_products(bot, chat_id, message_id, token_params)
        return "HANDLE_MENU"
    quantity, product_id = user_reply.split()
    product = get_product_from_cms(product_id, token_params)
    create_cart(token, chat_id)
    add_product_to_cart(token, product, chat_id, int(quantity))
    send_products(bot, chat_id, message_id, token_params)
    return "HANDLE_MENU"


def handle_cart(bot, update, token_params):
    token = f"Bearer {token_params['access_token']}"
    user_reply = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    if user_reply == "pay":
        bot.send_message(
            chat_id=chat_id,
            text="Введите e-mail"
        )
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        return "WAITING_EMAIL"
    if user_reply == "back":
        send_products(bot, chat_id, message_id, token_params)
        return "HANDLE_MENU"
    delete_item_from_cart(token=token, cart_id=chat_id, product_id=user_reply)
    send_cart(bot, chat_id, message_id, token_params)
    return "HANDLE_CART"


def handle_email(bot, update, token_params):
    token = f"Bearer {token_params['access_token']}"
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    bot.send_message(
        chat_id=chat_id,
        text=f"ваш e-mail: {update.message.text}",
    )
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    user = create_customer(
        token,
        name=update.message.from_user.username,
        e_mail=update.message.text
    )
    logger.info(user)
    

def handle_users_reply(bot, update, redis_db, token_params, client_params):
    current_time = time.time()
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
        "HANDLE_CART": handle_cart,
        "WAITING_EMAIL": handle_email,
    }
    state_handler = states_functions[user_state]
    if current_time > token_params["expires"]:
        token_params = get_token(
            client_params["client_id"],
            client_params["client_secret"]
        )
    try:
        next_state = state_handler(bot, update, token_params)
        redis_db.set(chat_id, next_state)
    except Exception as err:
        print(err)


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(format="%(asctime)s - %(lineno)d - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    redis_db = redis.Redis(
        host=os.getenv("REDIS_DB"),
        port=os.getenv("REDIS_PORT"),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )
    moltin_client_id = os.getenv("MOLTIN_CLIENT_ID")
    moltin_client_secret = os.getenv("MOLTIN_CLIENT_SECRET")
    moltin_token_params = get_token(moltin_client_id, moltin_client_secret)
    logger.info(moltin_token_params)
    bot_token = os.getenv("TG_BOT_TOKEN")
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            partial(
                handle_users_reply,
                redis_db=redis_db,
                token_params=moltin_token_params,
                client_params={
                    "client_id": moltin_client_id,
                    "client_secret": moltin_client_secret
                }
            )
        )
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(
                handle_users_reply,
                redis_db=redis_db,
                token_params=moltin_token_params,
                client_params={
                    "client_id": moltin_client_id,
                    "client_secret": moltin_client_secret
                }
            )
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            "start", 
            partial(
                handle_users_reply,
                redis_db=redis_db,
                token_params=moltin_token_params,
                client_params={
                    "client_id": moltin_client_id,
                    "client_secret": moltin_client_secret
                }
            )
        )
    )
    updater.start_polling()
    updater.idle()
