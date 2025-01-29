import json
import os
import time

from dotenv import load_dotenv
import boto3
from flask import Flask
from jira import JIRA

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
AWS_QUEUE = os.getenv("AWS_Q2")
JIRA_KEY = os.getenv("JIRA_KEY")
EMAIL = os.getenv("EMAIL")
HOST = os.getenv("HOST")
PROJECT_ID = os.getenv("PROJECT_ID")

sqs = boto3.client('sqs', region_name=AWS_REGION)

jira = JIRA(server=HOST, basic_auth=(EMAIL, JIRA_KEY))

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def home():
        print(f"{AWS_REGION} {AWS_QUEUE}")
        return "<h1>test</h1>", 200

    return app

def get_messages():
    print("TEST")
    print(f"{AWS_REGION} {AWS_QUEUE} {JIRA_KEY}")
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
                WaitTimeSeconds=0
            )

            message = response['Messages'][0]
            receipt_handle = message['ReceiptHandle']

            # Delete received message from queue
            sqs.delete_message(
                QueueUrl=AWS_QUEUE,
                ReceiptHandle=receipt_handle
            )
            print('Received and deleted message: %s' % message)

            body = message['Body']
            body = body.replace("\'", "\"") # WHY?????
            json_body = json.loads(body)
            print(f"Message contents {json_body}")
            print(f"Title: {json_body.get("title")}")

            send_jira_message(json_body)

        except:
            pass
        time.sleep(1)

def send_jira_message(json_body):
    # Issue data (replace with your own data)
    issue_data = {
        "project": {"key": PROJECT_ID},
        "summary": f"{json_body.get("title")}",
        "description": f"{json_body.get("desc")}",
        "issuetype": {"name": "Task"},
    }

    try:
        # Create the issue
        new_issue = jira.create_issue(fields=issue_data)

        # Print the key of the created issue
        print("Issue created successfully!")
        print("Issue Key:", new_issue.key)
    except Exception as e:
        print("Failed to create issue:", str(e))

if __name__ == '__main__':
    # app = create_app()
    # app.run()
    get_messages()
    pass
