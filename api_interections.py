import os
import logging

from dotenv import load_dotenv
import requests


logger = logging.getLogger("salesbot")

def delete_item_from_cart(token, cart_id, product_id):
    headers = {
        "Authorization": token,
    }
    url = f"https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}"
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_client_token(moltinapp_client_id):
    payload = {
        "client_id": moltinapp_client_id,
        "grant_type": "implicit"
    }
    response = requests.post(
        "https://api.moltin.com/oauth/access_token",
        data=payload
    )
    response.raise_for_status()
    return response.json()


def get_token(moltin_client_id, moltin_client_secret):
    payload = {
        "client_id": moltin_client_id,
        "client_secret": moltin_client_secret,
        "grant_type": "client_credentials"
    }
    response = requests.post(
        "https://api.moltin.com/oauth/access_token",
         data=payload
    )
    response.raise_for_status()
    return response.json()


def create_customer(token, name, e_mail):
    headers = {
        "Authorization": token,
    }
    payload = {
        "data": {
            "name": name,
            "email": e_mail,
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
                'amount': 530,
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
