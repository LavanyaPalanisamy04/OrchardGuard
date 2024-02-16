import boto3
from django.conf import settings

# from InternshipProject2 import settings

# Initialize Boto3 client for DynamoDB
dynamodb_client = boto3.client(
    'dynamodb',
    region_name=settings.AWS_DEFAULT_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

table_name  = 'AppleAccessions'

dynamodb_resource = boto3.resource(
    'dynamodb',
    region_name=settings.AWS_DEFAULT_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

# Reference the DynamoDB Table
table = dynamodb_resource.Table(table_name)

def insert_item_into_dynamodb(item):
    try:
        response = dynamodb_client.put_item(
            TableName='AppleAccessions',
            Item=item
        )
        print("Item inserted successfully:", response)
        return True
    except Exception as e:
        print("Error inserting item:", e)
        return False


def insert_data_into_dynamodb(data):
    try:
        with table.batch_writer() as batch:
            for item in data:
                print(item)
                batch.put_item(Item=item)
        print("Data inserted successfully")
    except Exception as e:
        print("Error inserting data:", e)

def query(queries):
    items = []
    for query in queries:
        response = table.query(
            IndexName=query['IndexName'],
            KeyConditionExpression=query['KeyConditionExpression'],
            ExpressionAttributeValues=query['ExpressionAttributeValues']
        )
        items.extend(response.get('Items', []))
    return items

def query_by_partition_key(acno):
    response = table.query(
        KeyConditionExpression='acno = :acno',
        ExpressionAttributeValues={':acno': acno}
    )
    print(response)
    return response.get('Items', [])