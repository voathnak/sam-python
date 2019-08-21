import json
import logging
import os
import time
import uuid
from datetime import datetime

import boto3

import decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE'])


class DecimalEncoder(json.JSONEncoder):  # This is a workaround for: http://bugs.python.org/issue16535
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)





def lambda_handler(event, context):
    print("event:", json.dumps(event, indent=4, sort_keys=True))

    print("context", context)

    # Get environment variables
    table_name = os.environ['TABLE']
    region = os.environ['REGION']

    existing_tables = boto3.client('dynamodb').list_tables()['TableNames']
    todo_table = boto3.resource('dynamodb', region_name=region).Table(table_name)
    # todo_table = boto3.resource('dynamodb', endpoint_url="http://localhost:8000/").Table(table_name)

    method = event.get('httpMethod', None)
    if method and method == 'GET':
        return list(todo_table, event, context)

    elif method and method == 'POST':
        return create(todo_table, event, context)

    elif method and method == 'PUT':
        return update(todo_table, event, context)


    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
        }),
    }


def list(table, event, context):


    # fetch all todos from the database
    result = table.scan()

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(result['Items'], cls=DecimalEncoder)
    }

    return response


def create(table, event, context):
    data = json.loads(event['body'])
    if 'text' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't create the todo item.")

    timestamp = str(datetime.utcnow().timestamp())


    item = {
        'id': str(uuid.uuid1()),
        'text': data['text'],
        'checked': False,
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }

    # write the todo to the database
    table.put_item(Item=item)

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(item)
    }

    return response


def delete(table, event, context):

    # delete the todo from the database
    table.delete_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )

    # create a response
    response = {
        "statusCode": 200
    }

    return response

def update(table, event, context):
    data = json.loads(event['body'])
    if 'text' not in data or 'checked' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't update the todo item.")

    timestamp = int(time.time() * 1000)


    # update the todos in the database
    result = table.update_item(
        Key={
            'id': event['pathParameters']['id']
        },
        ExpressionAttributeNames={
          '#todo_text': 'text',
        },
        ExpressionAttributeValues={
          ':text': data['text'],
          ':checked': data['checked'],
          ':updatedAt': timestamp,
        },
        UpdateExpression='SET #todo_text = :text, '
                         'checked = :checked, '
                         'updatedAt = :updatedAt',
        ReturnValues='ALL_NEW',
    )

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(result['Attributes'],
                           cls=DecimalEncoder)
    }

def get(table, event, context):

    # fetch todos from the database
    result = table.get_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(result['Item'],
                           cls=DecimalEncoder)
    }

    return response
