from dotenv import load_dotenv
import boto3
import requests
import json
import uuid
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import time
import os
import jwt

# Load Variables
load_dotenv()
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")
DB_TABLE_NAME = os.getenv("TABLE_NAME")
GOOGLE_NLP_API_KEY = os.getenv("GOOGLE_NLP_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_MAX_TRY_ATTEMPTS = os.getenv("TWILIO_MAX_TRY_ATTEMPTS")
TWILIO_DELAY_SEC = os.getenv("TWILIO_DELAY_SEC")
TWILIO_FROM = os.getenv("TWILIO_FROM")

# Connect to DB
dynamodb = boto3.client('dynamodb')


# Function for WhatsApp Message
def send_whatsapp_msg(text_message, recipient):
    response_message = text_message
    whatsappid = recipient
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    for attempt in range(1, int(TWILIO_MAX_TRY_ATTEMPTS) + 1):
        try:
            message = twilio_client.messages.create(
                from_=TWILIO_FROM,
                body=response_message,
                to=f'whatsapp:{whatsappid}',
                attempt=10
            )
            print("WhatsApp message sent successfully.")
            break  # Exit the loop if message sent successfully
        except TwilioRestException as e:
            print(f"Error sending WhatsApp message (attempt {attempt}):", e)
            if attempt < int(TWILIO_MAX_TRY_ATTEMPTS):
                print(f"Retrying in {int(TWILIO_DELAY_SEC)} seconds...")
                time.sleep(int(TWILIO_MAX_TRY_ATTEMPTS))
    else:
        print("Failed to send WhatsApp message after multiple attempts.")


def lambda_handler(event, context):
    # Extract Admin info
    print(event['headers'])
    token_id = event['headers']['Authorization']
    decoded_token = jwt.decode(token_id, algorithms=["RS256"], options={"verify_signature": False})
    print(decoded_token)
    support_email = decoded_token['email']
    print(support_email)

    # Parse the request body to extract ID and new value
    body = json.loads(event['body'])
    print(body)
    body_id = body.get('id')
    print(body_id)
    body_new_response_value = body.get('newresponse')
    print(body_new_response_value)

    # Check if ID and new value are provided
    if not body_id or not body_new_response_value:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'ID, Response and WhatsApp ID are required'})
        }

    try:
        # Retrieve the current value of the attribute
        current_response = dynamodb.get_item(
            TableName=DB_TABLE_NAME,
            Key={
                'id': {'S': body_id},
            },
            ProjectionExpression='FamilyName, GivenName, SupportResponse, whatsappid'
        )
        current_response_value = current_response.get('Item', {}).get('SupportResponse', {'S': ''})['S']
        familyname = current_response.get('Item', {}).get('FamilyName', {'S': ''})['S']
        givenname = current_response.get('Item', {}).get('GivenName', {'S': ''})['S']
        whatsappid = current_response.get('Item', {}).get('whatsappid', {'S': ''})['S']
        print(current_response_value, familyname, givenname, whatsappid)

        # Concatenate the new value with the current value
        timestamp = datetime.utcnow().isoformat()
        updated_response_value = f'{current_response_value}\n [{timestamp}] [By:{support_email}] {body_new_response_value}\n'
        print(updated_response_value)

        # Update the attribute in DynamoDB
        dynamodb.update_item(
            TableName=DB_TABLE_NAME,
            Key={
                'id': {'S': body_id},
            },
            UpdateExpression='SET SupportResponse = :val',
            ExpressionAttributeValues={':val': {'S': updated_response_value}}
        )
        response_msg = f'Dear {givenname} {familyname}, {body_new_response_value}.'
        print(response_msg)
        send_whatsapp_msg(response_msg, whatsappid)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Response Successfully Saved and WhatsApp Message Sent to Customer'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


