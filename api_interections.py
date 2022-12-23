import os
import argparse
import logging

from dotenv import load_dotenv
import requests


logger = logging.getLogger("salesbot")

def authorize(func):
    def wrapper(token, *args, **kwargs):
        try:
            result = func(token, *args, **kwargs)
        except:
            token = f"Bearer {get_token()['access_token']}"
            result = func(token, *args, **kwargs)
        finally:
            return result
    return wrapper


def get_client_token():
    payload = {
        "client_id": os.getenv("MOLTIN_APP_CLIENT_ID"),
        "grant_type": "implicit"
    }
    response = requests.post(
        "https://api.moltin.com/oauth/access_token",
        data=payload
    )
    response.raise_for_status()
    return response.json()


def get_token():
    payload = {
        "client_id": os.getenv("MOLTIN_CLIENT_ID"),
        "client_secret": os.getenv("MOLTIN_CLIENT_SECRET"),
        "grant_type": "client_credentials"
    }
    response = requests.post(
        "https://api.moltin.com/oauth/access_token",
         data=payload
    )
    response.raise_for_status()
    return response.json()


def create_customer(token):
    headers = {
        "Authorization": token,
    }
    payload = {
        "data": {
            "name": "Jack Sparrow",
            "password": "password",
            "email": "some_email@mail.com",
            "type": "customer",
        }
    }
    response = requests.post(
        "https://api.moltin.com/v2/customers",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def get_products(token):
    headers = {"Authorization": token}
    response = requests.get(
            "https://api.moltin.com/pcm/products",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_product(token, product_id):
    headers = {"Authorization": token}
    response = requests.get(
            f"https://api.moltin.com/pcm/products/{product_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def create_cart(token, cart_name):
    headers = {
        "Authorization": token,
    }
    payload = {
        "data": {
            "name": f"{cart_name}",
            "description": "How much is the fish?"
        }
    }
    response = requests.post(
        "https://api.moltin.com/v2/carts",
        json=payload,
        headers=headers
        )
    response.raise_for_status()
    return response.json()


def get_cart_items(token, cart_id):
    headers = {
        "Authorization": token,
    }
    response = requests.get(
        f"https://api.moltin.com/v2/carts/{cart_id}/items",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_cart(token, cart_id):
    headers = {
        "Authorization": token,
    }
    response = requests.get(
        f"https://api.moltin.com/v2/carts/{cart_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_cart_items(token, cart_id):
    headers = {
        "Authorization": token,
    }
    response = requests.get(
        f"https://api.moltin.com/v2/carts/{cart_id}/items",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def upload_product_image(token, file_url):
    headers = {
        "Authorization": token,
    }
    files = {"file_location": (None, file_url)}
    response = requests.post(
        "https://api.moltin.com/v2/files",
        headers=headers,
        files=files
    )
    return response.json()


def add_image_to_product(token, product_id, image_id):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    payload = {
        "data": 
            {
                "type": "file",
                "id": image_id
            },
    }
    response = requests.put(
        f"https://api.moltin.com/pcm/products/{product_id}/relationships/main_image",
        headers=headers,
        json=payload
    )
    return response.status_code


def get_file(token, file_id):
    headers = {
        "Authorization": token,
    }
    response = requests.get(
        f"https://api.moltin.com/v2/files/{file_id}",
        headers=headers
    )
    return response.json()


def add_product_to_cart(token, product, cart_id, quantity):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }

    json_data = {
        "data": {
            "type": "custom_item",
            "name": product["name"],
            'sku': product["sku"],
            'description': product["description"],
            "quantity": quantity,
            'price': {
                'amount': 30,
            },
        },
    }
    response = requests.post(
        f"https://api.moltin.com/v2/carts/{cart_id}/items",
        headers=headers,
        json=json_data
    )
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    token_params = get_token()
    client_token_params = get_client_token()
    token = f"Bearer {token_params['access_token']}"
    client_token = f"Bearer {client_token_params['access_token']}"
    logger.info(token)
    products = get_products(token)
    product = products["data"][1]
    # logger.info(product)
    loaded_image_id = product["relationships"]["main_image"]["data"]["id"]
    logger.info(loaded_image_id)
    """
    file_params = upload_product_image(
        token,
        "https://images.fineartamerica.com/images-medium-large-5/green-fish-wendy-j-st-christopher.jpg"
    )
    """
    # image_id = file_params["data"]["id"]
    # logger.info(image_id)
    # logger.info(add_image_to_product(token, product["id"], image_id))
    # logger.info(get_file(token, loaded_image_id))
    # logger.info(create_cart(token, "fishes"))
    # cart = get_cart(token, "fishes")
    # logger.info(get_cart(token, "196311441"))
    # logger.info(add_product_to_cart(token, product, "196311441", 3))


if __name__ == "__main__":
    main()
