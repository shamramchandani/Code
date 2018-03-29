""" Script to create, tag and delete snapshots of storage gateway volumes
Author: Barry Dawson, Sham Ramchandani & Mark Lightfoot
With lots of help from Alex Kinnane.
Script requires two parameters:
1: gw_arn  = The aws arn for the storage gateway
2: retention_days = The number of days to retain snapshot before deletion
Script can be executed from inside or outside Lambda
"""

import sys
import datetime
import os
import boto3


def get_sgw_volumes(gw_arn):
    """ Function to return list of volumes belonging to a storage gateway"""
    sgw = boto3.client('storagegateway')
    print("Getting volumes on", gw_arn)
    sgvols = sgw.list_volumes(GatewayARN=gw_arn)
    volcount = len(sgvols['VolumeInfos'])
    print(volcount, "volumes found")
    if volcount == 0:
        error_message = "Error - no volumes found for " + gw_arn
        print(error_message)
        raise Exception(error_message)
    return sgvols


def snapshot_sgw_volume(sgvol):
    """ Function to take snapshot of storage storage gateway volume"""
    sgw = boto3.client('storagegateway')
    print("Taking snapshot of", sgvol['VolumeId'])
    vol_snapshot = sgw.create_snapshot(
        SnapshotDescription='Snapshot of Storage Gateway Volume {0}'.format(sgvol['VolumeId']),
        VolumeARN=sgvol['VolumeARN']
    )
    print("Snapshot id is", vol_snapshot['SnapshotId'])
    return vol_snapshot


def tag_ec2_volume(vol_snapshot, gw_arn):
    """ Function to tag a storage gateway volume snapshot"""
    retention_days_str = os.environ['retention_days']
    #Get retention_days value from the serverless script
    retention_days = int(retention_days_str)
    ec2 = boto3.client('ec2')
    sgw = boto3.client('storagegateway')
    delete_date = datetime.date.today() + datetime.timedelta(retention_days)
    #Calculate the deletion date to put into tag
    delete_fmt = delete_date.strftime('%Y%m%d')
    print("Tagging", vol_snapshot['SnapshotId'], "with delete_date", delete_fmt)
    snap_tags = [
        {'Key': 'StorageGateway', 'Value': gw_arn},
        {'Key': 'DeleteOn', 'Value': delete_fmt},
    ]
    sgvol_tags = sgw.list_tags_for_resource(
        ResourceARN=vol_snapshot['VolumeARN']
        )['Tags']
    snap_tags.extend(sgvol_tags)
    ec2.create_tags(
        Resources=[
            vol_snapshot['SnapshotId'],
        ],
        Tags=snap_tags
    )


def get_old_ec2_snapshots(sgvol, tag_errors):
    """ Function to return list of snapshots that have passed the DeleteOn date"""
    snapshot_list = get_ec2_snapshots(sgvol)
    todays_date = datetime.datetime.today()
    todays_date_fmt = todays_date.strftime('%Y%m%d')
    print("Getting old snapshots that are ready for deletion")
    for snapshot in snapshot_list:
        try:
            tags = {}
            for tag in snapshot["Tags"]:
                tags[tag["Key"]] = tag["Value"]
            snapshot["Tags"] = tags
        except KeyError:
            pass
    old_snapshots = []
    for snapshot in snapshot_list:
        try:
            if (snapshot["Tags"]["DeleteOn"]) < todays_date_fmt:
                print("snap tag is", snapshot["Tags"]["DeleteOn"])
                old_snapshots.append(snapshot)
        except KeyError:
            print("Warning! Unable to check DeleteOn date for", snapshot['SnapshotId'])
            tag_errors += 1
    return old_snapshots, tag_errors


def delete_ec2_snapshots(old_snapshots):
    """Function to delete ec2 snapshots"""
    snaps_to_delete = len(old_snapshots)
    if snaps_to_delete == 0:
        print("No old snapshots to be deleted")
    else:
        print(snaps_to_delete, "snapshots to be deleted")
        ec2 = boto3.client('ec2')
        for snapshot in old_snapshots:
            print("Deleting snapshot with id " + snapshot["SnapshotId"])
            ec2.delete_snapshot(SnapshotId=snapshot["SnapshotId"])


def get_ec2_snapshots(sgvol):
    """ Function to get list of snapshots belonging to specific ec2 volume"""
    print("Getting snapshots on", sgvol['VolumeId'])
    ec2 = boto3.client('ec2')
    filters = [
        {'Name': 'volume-id', 'Values': [sgvol['VolumeId']]}
    ]
    snapshot_response = ec2.describe_snapshots(Filters=filters)
    snap_count = len(snapshot_response['Snapshots'])
    print(snap_count, "snapshots found")
    return snapshot_response['Snapshots']


def sgw_snap_tag_delete_vols():
    """ Function to create, tag and delete snapshots of storage gateway volumes"""
    tag_errors = 0
    gw_arn = os.environ['gw_arn']
    #Gets gateway ARN from the serverless script depending upon environment being deployed to
    sgvols = get_sgw_volumes(gw_arn)
    for sgvol in sgvols['VolumeInfos']:
        vol_snapshot = snapshot_sgw_volume(sgvol)
        tag_ec2_volume(vol_snapshot, gw_arn)
        old_snapshots, tag_errors = get_old_ec2_snapshots(sgvol, tag_errors)
        delete_ec2_snapshots(old_snapshots)
    return tag_errors


def lambda_handler(event, context):
    """If started from Lambda, this will run"""
    print(event)
    print(context)
    tag_errors = sgw_snap_tag_delete_vols()
    if tag_errors:
        raise Exception(str(tag_errors) + " snapshots found without correct DeleteOn tag")


if __name__ == "__main__":
    #If started from outside Lambda, this will run
    TAG_ERRORS = sgw_snap_tag_delete_vols()
    sys.exit(TAG_ERRORS)
