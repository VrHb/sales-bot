import os
from pprint import pprint
import logging
from functools import partial

import redis

from dotenv import load_dotenv

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, CallbackQueryHandler, \
    CommandHandler, MessageHandler 

from api_interections import add_product_to_cart, get_token, get_products, get_product, get_file, get_cart_items, get_cart, create_cart


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
    keyboard.append([InlineKeyboardButton("Корзина", callback_data="cart")])
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
        "id": product_params["id"],
        "name": product_params["attributes"]["name"],
        "sku": product_params["attributes"]["sku"],
        "description": product_params["attributes"]["description"],
        "image_link": image_link,
    }


def handle_menu(bot, update):
    token_params = get_token()
    token = f"Bearer {token_params['access_token']}"
    user_reply = update.callback_query.data
    if user_reply == "cart":
        
        # The same logic in start state (in one func mb)

        chat_id = update.callback_query.message.chat_id
        cart_params = ""
        items = get_cart_items(token, str(chat_id))["data"]
        keyboard = []
        for item in items:
            
            # fix this strinf method

            cart_params += f"{item['name']}\n{item['description']}\n{item['meta']['display_price']['with_tax']['unit']['formatted']} per kg\n{item['quantity']} kg in cart for {item['meta']['display_price']['with_tax']['value']['formatted']}\n\n"
            keyboard.append(
                [InlineKeyboardButton(
                    f"Убрать из корзины {item['name']}",
                    callback_data=item["id"]
                )]
            )
        keyboard.append([InlineKeyboardButton(f"В меню", callback_data="back")])
        total_price = get_cart(token, str(chat_id))["data"]["meta"]["display_price"]["with_tax"]["formatted"]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            chat_id=chat_id,
            text=cart_params + f" Total: {total_price}",
            reply_markup=reply_markup,
        )
        return "HANDLE_CART"
    product_id = update.callback_query.data
    product = get_product_from_cms(product_id)
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    keyboard = [
        [
            InlineKeyboardButton("1 кг", callback_data=f"1 {product_id}"),
            InlineKeyboardButton("5 кг", callback_data=f"5 {product_id}"),
            InlineKeyboardButton("10 кг", callback_data=f"10 {product_id}")
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
    token_params = get_token()
    token = f"Bearer {token_params['access_token']}"
    user_reply = update.callback_query.data
    logger.info(user_reply)
    if user_reply == "back":
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
        chat_id = update.callback_query.message.chat_id
        message_id = update.callback_query.message.message_id
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        bot.send_message(
            chat_id=chat_id,
            text="Choose:",
            reply_markup=reply_markup
        )
        return "HANDLE_MENU"
    quantity, product_id = user_reply.split()
    chat_id = update.callback_query.message.chat_id
    product = get_product_from_cms(product_id)
    create_cart(token, chat_id)
    add_product_to_cart(token, product, chat_id, int(quantity))
    return "HANDLE_DESCRIPTION"


def handle_cart(bot, update):
    user_reply = update.callback_query.data
    if user_reply == "back":
        return "HANDLE_MENU"
    
    # Add delete logic for items


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
        "HANDLE_CART": handle_cart
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
