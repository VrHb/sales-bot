import os
import argparse
import logging

from dotenv import load_dotenv
import requests


logger = logging.getLogger("salesbot")

def get_token():
    payload = {
        "client_id": os.getenv("MOLTIN_CLIENT_ID"),
        "client_secret": os.getenv("MOLTIN_CLIENS_SECRET"),
        "grant_type": "client_credentials"
    }
    response = requests.post(
        "https://api.moltin.com/oauth/access_token",
         data=payload
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


def main():
    load_dotenv()
    moltin_token = os.getenv("MOLTIN_API_TOKEN")
    print(moltin_token)
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    parser = argparse.ArgumentParser(
        description="Получение товаров"
    )
    parser.add_argument(
        "--url",
        default="url",
        help="url адрес ресурса"
    )
    args = parser.parse_args()
    logger.info(get_products(moltin_token))


if __name__ == "__main__":
    main()
