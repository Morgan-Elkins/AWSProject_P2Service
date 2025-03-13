import json
import os
import threading
import time

from dotenv import load_dotenv
import boto3
from flask import Flask, jsonify
from jira import JIRA

from botocore.exceptions import ClientError

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
AWS_QUEUE = os.getenv("AWS_Q2")
JIRA_KEY = os.getenv("JIRA_KEY")
EMAIL = os.getenv("EMAIL")
HOST = os.getenv("HOST")
PROJECT_ID = os.getenv("PROJECT_ID")

sqs = boto3.client('sqs', region_name=AWS_REGION)

app = Flask(__name__)

# Bedrock client

bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="eu-west-2"
)

model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

def getLLMmessage(userMessage):
    # Start a conversation with the user message.
    user_message = userMessage
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]

    try:
        # Send the message to the model, using a basic inference configuration.
        response = bedrock_client.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        )

        # Extract and print the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text
    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        return ""


# http://localhost:5002/health
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"Healthy"}), 200

def get_messages():
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=AWS_QUEUE,
                AttributeNames=[
                    'SentTimestamp'
                ],
                MaxNumberOfMessages=1,
                MessageAttributeNames=[
                    'All'
                ],
                VisibilityTimeout=0,
                WaitTimeSeconds=2
            )

            message = response['Messages'][0]
            receipt_handle = message['ReceiptHandle']

            # Delete received message from queue
            sqs.delete_message(
                QueueUrl=AWS_QUEUE,
                ReceiptHandle=receipt_handle
            )

            body = message['Body']
            json_body = eval(body)
            print(f"Message contents {json_body}")

            if json_body.get("title") is None or json_body.get("desc") is None or json_body.get("prio") is None:
                continue

            send_jira_message(json_body)

        except:
            pass

def send_jira_message(json_body):
    get_llm_message = f"   \n\n **A suggested improvement is**: {getLLMmessage(str(json_body.get('desc')))}"
    issue_data = {
        "project": {"key": PROJECT_ID},
        "summary": f"{json_body.get('title')}",
        "description": f"{json_body.get('desc')}   \n {get_llm_message}",
        "issuetype": {"name": "Task"},
    }

    jira = JIRA(server=HOST, basic_auth=(EMAIL, JIRA_KEY))

    try:
        # Create the issue
        new_issue = jira.create_issue(fields=issue_data)

        # Print the key of the created issue
        print("Issue created successfully!")
        print("Issue Key:", new_issue.key)
        return "Issue created successfully!"
    except Exception as e:
        print("Failed to create issue:", str(e))
        return "Failed to create issue:"

def background_thread():
    thread = threading.Thread(target=get_messages, daemon=True)
    thread.start()
    return thread

bg_thread = background_thread()

#Docker: docker run --env-file ./.env -p 8082:8082 --rm p2service-flask-app
if __name__ == '__main__':
    threading.Thread(target=lambda: app.run()).start()
