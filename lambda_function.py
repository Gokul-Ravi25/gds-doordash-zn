import pandas as pd
import json
import boto3


def lambda_handler(event, context):
    # Extracting bucket name and object key from S3 event
    print(event)
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        object_key = event['Records'][0]['s3']['object']['key']
    except KeyError as e:
        publish_to_sns(
            "Failed to extract bucket name or object key from S3 event: {}".format(str(e)))
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to extract bucket name or object key from S3 event')
        }

    print(bucket_name, object_key)
    # Read the JSON file from S3 into a pandas DataFrame
    try:
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket_name, Key=object_key)
        df = pd.read_json(obj['Body'])
        print(df)
    except Exception as e:
        publish_to_sns("Failed to read JSON file from S3: {}".format(str(e)))
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to read JSON file from S3')
        }

    # Filter records where status is "delivered"
    filtered_df = df[df['status'] == 'delivered']
    print(filtered_df)
    # Write the filtered DataFrame to a new JSON file
    output_bucket = 'aws-doordash-target-zn'
    output_object_key = 'File_delivered.json'  # Setting the output file name
    output_file_path = f's3://{output_bucket}/{output_object_key}'
    print(output_file_path)
    # Convert DataFrame to JSON string
    json_string = filtered_df.to_json(
        orient='records', lines=True, index=False)
    try:
        s3.put_object(Bucket=output_bucket,
                      Key=output_object_key, Body=json_string)
        print("File is loaded to the new S3")
    except Exception as e:
        publish_to_sns(
            "Failed to write filtered DataFrame to S3: {}".format(str(e)))
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to write JSON file to S3')
        }

    # Publish success message to SNS topic
    publish_to_sns(
        "Successfully filtered records and wrote to S3: {}".format(output_file_path))

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully filtered records and wrote to S3')
    }


def publish_to_sns(message):
    sns = boto3.client('sns')
    # Replace with your SNS topic ARN
    topic_arn = 'arn:aws:sns:us-east-1:661916559814:doordash-notification'
    sns.publish(
        TopicArn=topic_arn,
        Message=message
    )
