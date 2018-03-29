""" Script to get ssm task output from logs in s3 and post to slack
If multiple versions of same log file exist in s3, ony new content will be posted
Versioning must be enabled on the bucket for correct functionality
Python 3
"""

import json
import os
import boto3
import requests

def lambda_handler(event, context):
    # Lambda calls this function

    s3res = boto3.resource('s3')
    url = os.environ['webhookurl']

    def s3_to_list(s3_obj_version):
        # Function to get body text of specific version of S3 object and return it as list
        s3_obj = s3_obj_version.get()
        body = s3_obj['Body'].read().decode('utf-8')
        print(body)
        body_list = body.splitlines(keepends=True)
        return body_list

    for record in event['Records']:
        
        # Get the S3 bucket name and key, then count how many versions of the key exist
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        bucket_obj = s3res.Bucket(bucket)
        versions = list(bucket_obj.object_versions.filter(Prefix=key))
        version_count = len(versions)
        print(str(version_count) + ' versions of ' + key + ' found')
        
        # Get current version of S3 key, convert to list then count lines
        curr = versions[0]
        curr_list = s3_to_list(curr)
        curr_len = len(curr_list)
        print('Current version of file has ' + str(curr_len) + ' lines')
        
        # If previous version exists, get it and count the lines.  If not, set line count to zero
        if version_count > 1:
            prev = versions[1]
            prev_list = s3_to_list(prev)
            prev_len = len(prev_list)
            print('Previous version of file has ' + str(prev_len) + ' lines')
        else:
            prev_len = 0
        
        # If current and previous versions are the same length, do nothing
        # Otherwise process the list to produce a single string containing only new lines
        if curr_len == prev_len:
            print('Current and previous versions of the file are the same.  Nothing to do')
            continue
        else:
            print('Processing the following range: ' + str(curr_len - prev_len) + ' to ' + str(curr_len))
            task_output = ""
            for i in range(prev_len, curr_len):
                task_output += curr_list[i]
            print('Task output is...')
            print(task_output)
        
        # Set colour of slack message according to content of task output
        if "ERROR" in task_output:
            message_colour = "danger"
        elif "WARNING" in task_output:
            message_colour = "warning"
        else:
            message_colour = "good"
        
       # Split the S3 key to get the ssm instance-id and task name, then assemble the title message for slack
        splitkey = key.split('/')
        instance = splitkey[-3]
        if instance == 'awsrunPowerShellScript':
            instance  = splitkey[-4]
        task_name = splitkey[-2]
        task_title = "SSM-Instance:" + instance + " SSM-Task:" + task_name
        print('Task title set to: ' + task_title)

        # the json message for posting to slack
        message = {"text":task_title, "attachments":[{"color":message_colour, "text":task_output}]}

        # post the message to slack
        params = json.dumps(message)
        requests.post(url, data=params, headers={'content-type': 'application/json'})

