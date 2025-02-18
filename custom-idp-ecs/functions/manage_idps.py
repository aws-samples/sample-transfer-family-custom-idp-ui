from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import event_source, ALBEvent
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from dataclasses import dataclass
import boto3
import simplejson as json
import os

logger = Logger()
metrics = Metrics()
tracer = Tracer()

table_name = os.environ['IDP_TABLE_NAME']

ddb_client = boto3.resource("dynamodb")

@tracer.capture_lambda_handler
@metrics.log_metrics
@event_source(data_class=ALBEvent)
def handler(event: ALBEvent, context: LambdaContext):
    for key in event:
        logger.debug(f"{key}: {event[key]}")

    http_method = event['httpMethod']
    if http_method == "OPTIONS":
        return options()
    elif http_method == "GET":
        return get(event)
    elif http_method == "PUT":
        return put(event)
    elif http_method == "DELETE":
        return delete(event)
    else:
        return unsupported_method(http_method)

def unsupported_method(method):
    return {
        "isBase64Encoded": False,
        "statusCode": 400,
        "statusDescription": "405 Method Not Allowed",
        "headers": {
            "Content-Type": "application/json",
        },
        "body": f"{method} is not supported"
    }

def get(event):
    provider = event['path'].replace("/api/idp/", "")
    logger.info(f"get request parameters: {provider}")
    """
    Get all IDPs, or single IDP by ID
    :param event: if contains a single ID, it will be returned, otherwise a list returned
    :return: http response with IDP(s)
    """
    body = None
    table = ddb_client.Table(table_name)
    if provider:
        response = table.get_item(Key={'provider':provider})
        body = response['Item']
    else:
        response = table.scan()
        body = response['Items']
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "statusDescription": "200 OK",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # this should be ELB URL
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,GET"
        },
        "body": json.dumps(body)
    }

def put(event):
    """
    Persists an IDP
    :param event:
    :param event: must contain an IDP provider name (partition key)
    :return: http response indicating success or failure
    """
    body = json.loads(event['body'])
    logger.info(f"put request: {body}")
    # Todo implement dataclass by provider module to enforce payload structure validation
    table = ddb_client.Table(table_name)
    response = table.put_item(Item=body)
    dumps = json.dumps(response)
    logger.info(f"return put result: {dumps}")
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "statusDescription": "200 OK",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # this should be ELB URL
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,PUT"
        },
        "body": dumps
    }

def delete(event):
    """
    Delete IDP record specified in event
    :param event: must contain an IDP provider name (partition key)
    :return: http response indicating success or failure
    """""
    provider = event['path'].replace("/api/idp/", "")
    logger.info(f"delete request parameters: {provider}")
    table = ddb_client.Table(table_name)
    response = table.delete_item(Key={'provider':provider})
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "statusDescription": "200 OK",
        "headers": {
            "Content-Type": "application/json",  # this should be ELB URL
            "Access-Control-Allow-Origin": "*",  # this should be ELB URL
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,DELETE"
        },
        "body": json.dumps(response)
    }

def options():
    """
    Support for CORS preflight request for localhost and ELB endpoints
    :return: formatted http response
    """
    logger.debug("OPTIONS")
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "statusDescription": "200 OK",
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # this should be ELB URL
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,PUT,DELETE,GET"
        }
    }


@dataclass
class BaseIdp:
    module: str
    provider: str


@dataclass
class ArgonConfig:
    ssl: str
    ssl_verify: str


@dataclass
class CognitoConfig(BaseIdp):
    cognito_client_id: str
    cognito_user_pool_region: str
    domain: str
    scope: str