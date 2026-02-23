import json
import logging
import random
import os
import requests
import time

logger = logging.getLogger(__name__)

# ====================== TIKTOK SHOP INTEGRATION ======================

def fetch_tiktok_order(order_id: str):
    """
    Fetches order details from TikTok Shop API using App Key and Secret.
    """
    app_key = os.getenv("TIKTOK_APP_KEY")
    app_secret = os.getenv("TIKTOK_APP_SECRET")
    access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    
    if not all([app_key, app_secret, access_token]):
        logger.warning("TikTok credentials missing (specifically TIKTOK_ACCESS_TOKEN). Falling back to mock data.")
        return mock_tiktok_order(order_id)

    # Simplified TikTok API call structure
    url = f"https://open-api.tiktokglobalshop.com/api/orders/detail/query"
    params = {
        "app_key": app_key,
        "access_token": access_token,
        "timestamp": int(time.time()),
        "order_id_list": json.dumps([order_id])
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("code") == 0 and data.get("data", {}).get("order_list"):
            order_data = data["data"]["order_list"][0]
            addr = order_data.get("recipient_address", {})
            return {
                "order_id": order_id,
                "customer": {
                    "first_name": addr.get("name", "Customer"),
                    "email": order_data.get("buyer_email", ""),
                    "birth_date": "1991-02-17" # Placeholder: TikTok doesn't provide birthdate by default
                },
                "shipping_address": {
                    "name": addr.get("name"),
                    "address_line1": addr.get("address_line1"),
                    "city": addr.get("city"),
                    "state": addr.get("state"),
                    "zip_code": addr.get("zip_code"),
                    "country": "US"
                }
            }
    except Exception as e:
        logger.error(f"TikTok API Error: {e}")
        
    return mock_tiktok_order(order_id)

def mock_tiktok_order(order_id):
    logger.info(f"Using mock data for order {order_id}")
    return {
        "order_id": order_id,
        "customer": {"first_name": "Cassidy", "birth_date": "1991-02-17"},
        "shipping_address": {
            "name": "Cassidy Williams", 
            "address_line1": "123 Mystic Lane", 
            "city": "Portland", 
            "state": "OR", 
            "zip_code": "97204",
            "country": "US"
        }
    }

# ====================== LOB INTEGRATION ======================

def send_letter_via_lob(pdf_path: str, address: dict):
    """
    Sends a physical letter via Lob API using the provided API Key.
    """
    api_key = os.getenv("LOB_API_KEY")
    if not api_key:
        logger.error("LOB_API_KEY not found in environment.")
        return {"id": "MOCK_LOB_ID", "status": "mocked"}

    url = "https://api.lob.com/v1/letters"
    
    # Lob payload structure
    data_payload = {
        "description": f"Analog Algorithm Letter for {address['name']}",
        "to[name]": address["name"],
        "to[address_line1]": address["address_line1"],
        "to[address_city]": address["city"],
        "to[address_state]": address["state"],
        "to[address_zip]": address["zip_code"],
        "to[address_country]": "US",
        "from[name]": "Analog Algorithm",
        "from[address_line1]": "PO BOX 123",
        "from[address_city]": "Portland",
        "from[address_state]": "OR",
        "from[address_zip]": "97201",
        "from[address_country]": "US",
        "color": "true"
    }

    try:
        with open(pdf_path, 'rb') as f:
            files = {"file": f}
            response = requests.post(url, auth=(api_key, ""), data=data_payload, files=files)
            
        result = response.json()
        if response.status_code == 200:
            logger.info(f"Letter sent via Lob! ID: {result['id']}")
            return result
        else:
            logger.error(f"Lob Error: {result.get('error', {}).get('message')}")
            return {"id": "ERROR", "status": "failed"}
            
    except Exception as e:
        logger.error(f"Lob Integration Error: {e}")
        return {"id": "ERROR", "status": "failed"}
