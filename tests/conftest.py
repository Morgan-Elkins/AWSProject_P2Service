import os
import boto3
import pytest
from moto import mock_aws

os.environ['AWS_REGION'] = 'eu-west-2'
os.environ['AWS_Q2'] = 'testing'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['JIRA_KEY'] = 'testing'
os.environ['EMAIL'] = 'testing'
os.environ['PROJECT_ID'] = 'testing'

from app import send_jira_message, app


@pytest.fixture(scope='function')
def client():
    with mock_aws():
        sqs = boto3.client('sqs', region_name='eu-west-2')

        queue_url = sqs.create_queue(
            QueueName='testing'
        )['QueueUrl']

        yield sqs


def test_get_health(client):
    response = app.test_client().get("/health")
    assert b'{"status":"Healthy"}\n' in response.data

# @mock_aws()
# def test_sending_jira_message(client):
#     data = {"title": "pytest", "desc": "pytest desc", "prio": 0}
#     response = send_jira_message(data)
#     assert response == "Issue created successfully!"