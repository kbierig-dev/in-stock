import urllib.request
import urllib.parse
import json
import os
import boto3


def lambda_handler(event, context):
    url = os.environ.get("URL", None)

    # Payload details dynamically pulled from Environment Variables if they exist
    payload = {
        "action": "add_to_cart",
        "appid": int(os.environ.get("APP_ID", None)),
        "subid": int(os.environ.get("SUB_ID", None)),
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    data = urllib.parse.urlencode(payload).encode("ascii")
    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_text = response.read().decode("utf-8")

            try:
                resp_data = json.loads(response_text)
                if resp_data.get("success"):
                    body_message = f"SUCCESS! The item was added. Current cart item count: {resp_data.get('itemcount')}"
                    
                    try:
                        sns = boto3.client("sns")
                        phone_number = os.environ.get("PHONE_NUMBER")
                        if phone_number:
                            sns.publish(PhoneNumber=phone_number, Message=body_message)
                    except Exception as e:
                        print(f"Failed to send SMS: {e}")

                    return {
                        "statusCode": 200,
                        "body": body_message,
                    }
                else:
                    return {
                        "statusCode": 400,
                        "body": f"FAILED to add item. Site responded with: {resp_data}. Item may be Out of Stock or you are missing sessionid cookies.",
                    }
            except json.JSONDecodeError:
                return {
                    "statusCode": status_code,
                    "body": f"Response wasn't JSON. Text snippet: {response_text[:200]}",
                }

    except urllib.error.URLError as e:
        return {"statusCode": 500, "body": f"An error occurred: {str(e)}"}


if __name__ == "__main__":  # pragma: no cover
    # Local testing execution wrapper
    print(lambda_handler(None, None))
