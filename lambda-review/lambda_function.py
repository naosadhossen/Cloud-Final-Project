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

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION_NAME)
table = dynamodb.Table(DB_TABLE_NAME)


# AWS Sentiment Analyzer
def analyze_sentiment_aws(text):
    # Initialize AWS Comprehend client
    comprehend = boto3.client(service_name='comprehend', region_name=AWS_REGION_NAME)

    # Call AWS Comprehend
    response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
    aws_sentiment = response['Sentiment']

    return aws_sentiment


# Google Sentiment Analyzer
def analyze_sentiment_google(text):
    # Define the API endpoint URL
    url = f"https://language.googleapis.com/v1/documents:analyzeSentiment?key={GOOGLE_NLP_API_KEY}"

    # Define the request payload
    text_content = "Google Cloud Natural Language API sucks"
    payload = {
        "document": {
            "type": "PLAIN_TEXT",
            "content": text
        }
    }

    # Make the POST request to the API endpoint
    response = requests.post(url, json=payload)

    # Parse the response JSON
    response_json = response.json()
    google_sentiment = response_json['documentSentiment'].get('score')

    return google_sentiment

# Send WhatsApp Message
def send_whatsapp_msg(text_message, recepient):
    response_message = text_message
    whatsappid = recepient
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    for attempt in range(1, int(TWILIO_MAX_TRY_ATTEMPTS) + 1):
        try:
            message = twilio_client.messages.create(
                from_='whatsapp:+14155238886',
                body=response_message,
                to=f'whatsapp:{whatsappid}',
                attempt=10
            )
            print("WhatsApp message sent successfully.")
            break  # Exit the loop if message sent successfully
        except TwilioRestException as e:
            print(f"Error sending WhatsApp message (attempt {attempt}):", e)
            if attempt < int(TWILIO_MAX_TRY_ATTEMPTS):
                print(f"Retrying in {TWILIO_DELAY_SEC} seconds...")
                time.sleep(int(TWILIO_DELAY_SEC))
    else:
        print("Failed to send WhatsApp message after multiple attempts.")


def lambda_handler(event, context):
    # Get email address from token
    print(event['headers'])
    token_id = event['headers']['Authorization']
    decoded_token = jwt.decode(token_id, algorithms=["RS256"], options={"verify_signature": False})
    print(decoded_token)
    useremail = decoded_token['email']
    whatsappid = decoded_token['phone_number']

    # Get user's given name and family name from Toekn
    idp_client = boto3.client('cognito-idp', region_name=AWS_REGION_NAME)
    userinfo_response = idp_client.admin_get_user(
        UserPoolId='eu-central-1_HWPGNhtNT',
        Username=useremail
    )
    print(userinfo_response)
    userattributes = userinfo_response['UserAttributes']
    family_name = next((attr['Value'] for attr in userattributes if attr['Name'] == 'family_name'), None)
    given_name = next((attr['Value'] for attr in userattributes if attr['Name'] == 'given_name'), None)
    print(family_name, given_name)
    # Get Feedback
    body = json.loads(event['body'])
    feedback = body['text']

    # Call sentiment analysis functions
    aws_sentiment = analyze_sentiment_aws(feedback)
    google_sentiment = analyze_sentiment_google(feedback)

    # Ensemble method: Majority Voting
    if aws_sentiment == 'POSITIVE' and google_sentiment > 0.0:
        final_sentiment = 'POSITIVE'
    elif aws_sentiment == 'NEGATIVE' and google_sentiment < 0.0:
        final_sentiment = 'NEGATIVE'
        message = (f'Dear {given_name} {family_name}, Thanks for the feedback. '
                   f'From the feedback we understood that you are not satisfied with our product. '
                   f'One of our customer support will contact you to find out the problem. '
                   f'Thanks again for choosing our product and we hope to serve you better everytime.')
        send_whatsapp_msg(message, whatsappid)
    else:
        final_sentiment = 'NEUTRAL'

    # Store data in DynamoDB
    serviceid = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    table.put_item(
        Item={
            'id': serviceid,
            'CreateTime': timestamp,
            'FamilyName': family_name,
            'GivenName': given_name,
            'email': useremail,
            'whatsappid': whatsappid,
            'Feedback': feedback,
            'FinalSentiment': final_sentiment,
            'AWSSentiment': aws_sentiment,
            'GoogleSentiment': str(google_sentiment),
            'SupportResponse': ""
        }
    )

    # Create JSON response
    response = {
        'sentiment': final_sentiment,
        'ServiceID': serviceid
    }

    # Return JSON response
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }

