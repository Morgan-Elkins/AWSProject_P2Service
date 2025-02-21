import json
import os
import threading
import time

from dotenv import load_dotenv
import boto3
from flask import Flask, jsonify
from jira import JIRA

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
AWS_QUEUE = os.getenv("AWS_Q2")
JIRA_KEY = os.getenv("JIRA_KEY")
EMAIL = os.getenv("EMAIL")
HOST = os.getenv("HOST")
PROJECT_ID = os.getenv("PROJECT_ID")

sqs = boto3.client('sqs', region_name=AWS_REGION)

app = Flask(__name__)

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
    issue_data = {
        "project": {"key": PROJECT_ID},
        "summary": f"{json_body.get('title')}",
        "description": f"{json_body.get('desc')}",
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
