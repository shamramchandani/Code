""" This script checks the status of the StorageGateway
Author: Barry Dawson & Sham Ramchandani
Script requires two parameters:
1: gw_arn  = The aws arn for the storage gateway
2: retention_days = The number of days to retain snapshot before deletion
Script can be executed from inside or outside Lambda
"""

import os
import boto3


def storage_gateway_status():
    """This function looks at the status of the Gateway"""
    gw_arn = os.environ['gw_arn']
    #Gets gateway ARN from the serverless script depending upon environment being deployed to

    sgw = boto3.client('storagegateway')
    sgw_info = sgw.describe_gateway_information(
        GatewayARN=gw_arn
    )

    sgw_state = sgw_info['GatewayState']
    print(sgw_state)
    if sgw_state != 'RUNNING':
        error_message = "Warning, Storage Gateway is " + sgw_state
        raise Exception(error_message)
    return sgw_state

def lambda_handler(event, context):
    """If started from Lambda, this will run"""
    print(event)
    print(context)
    storage_gateway_status()
    
if __name__ == "__main__":
    #If started from outside Lambda, this will run
    storage_gateway_status()
