import subprocess
import json
import boto3

REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-2",
    "eu-west-1",
    "eu-north-1",
    "ap-southeast-1",
    "eu-central-1"]

profiles_raw = subprocess.check_output(['aws', 'configure', 'list-profiles'])
profiles = [s.decode('utf-8') for s in profiles_raw.split()]


for profile in profiles:
    if 'WbdClusterEng' in profile:
        sess = boto3.Session(profile_name=profile)
        for region in REGIONS:
            eks = sess.client('eks', region_name=region)
            region_clusters = eks.list_clusters()
            for cluster in region_clusters['clusters']:
                config = subprocess.check_output(['aws', 'eks', 'update-kubeconfig', '--profile', profile, '--region', region, '--name', cluster])
                print(config)