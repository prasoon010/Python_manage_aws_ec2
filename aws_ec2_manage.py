import boto3
from botocore.exceptions import ClientError
from prettytable import PrettyTable
import threading
import sys

ec2 = boto3.client('ec2')
d_regions = ec2.describe_regions()
all_regions = []
threadlist = []
insta_list = {}
x = PrettyTable()
x.border = False
x.field_names = ['Region/AZ', 'Name', 'Id', 'Type', 'State', 'Public IP',
                 'AMI Id', 'Key', 'Security group', 'Launch Time']


def startinsta(insta_id, region):
    ec2 = boto3.client('ec2', region_name=region)
    try:
        ec2.start_instances(InstanceIds=[insta_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise
    try:
        response = ec2.start_instances(InstanceIds=[insta_id], DryRun=False)
        print('Success', response)
        insta_list[insta_id]['state'] = 'running'

    except ClientError as e:
        print('Error', e)


def stopinsta(insta_id, region):
    ec2 = boto3.client('ec2', region_name=region)
    try:
        ec2.stop_instances(InstanceIds=[insta_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise
    try:
        response = ec2.stop_instances(InstanceIds=[insta_id], DryRun=False)
        print('Success', response)
        insta_list[insta_id]['state'] = 'stopped'

    except ClientError as e:
        print('Error', e)


def rebootinsta(insta_id, region):
    ec2 = boto3.client('ec2', region_name=region)
    try:
        ec2.reboot_instances(InstanceIds=[insta_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            print('You do not have permission to reboot')
            raise
    try:
        response = ec2.reboot_instances(InstanceIds=[insta_id], DryRun=False)
        print('Success', response)
    except ClientError as e:
        print('Error', e)


def terminateinsta(insta_id, region):
    ec2 = boto3.client('ec2', region_name=region)
    try:
        ec2.terminate_instances(InstanceIds=[insta_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            print('You do not have permission to terminate')
            raise
    try:
        response = ec2.terminate_instances(InstanceIds=[insta_id], DryRun=False)
        print('Success', response)
        insta_list[insta_id]['state'] = 'terminated'
    except ClientError as e:
        print('Error', e)


def insta(region):
    ec2r = boto3.resource('ec2', region_name=region)
    for i in ec2r.instances.all():
        ids = i.id
        insta_list[ids] = {}
        insta_list[ids]['Region'] = region
        insta_list[ids]['tag'] = tags = i.tags[0]['Value']
        insta_list[ids]['type'] = ty = i.instance_type
        insta_list[ids]['state'] = st = i.state['Name']
        insta_list[ids]['IP'] = ips = i.public_ip_address
        insta_list[ids]['image_id'] = img = i.image_id
        insta_list[ids]['key'] = key = i.key_name

        if st == 'terminated':
            insta_list[ids]['security_group'] = sg = 'None'
            insta_list[ids]['AZ'] = az = 'None'
        else:
            insta_list[ids]['security_group'] = sg = i.security_groups[0]['GroupName']
            insta_list[ids]['AZ'] = az = i.subnet.availability_zone

        insta_list[ids]['launch_time'] = lt = i.launch_time.strftime("%Y-%m-%d_%H:%M:%S")
        x.add_row([az, tags, ids, ty, st, ips, img, key, sg, lt])


print("Listing all Instances:\n")

for item in d_regions['Regions']:
    region = item['RegionName']
    all_regions.append(region)

for region in all_regions:
    t = threading.Thread(target=insta, args=(region,))
    t.start()
    threadlist.append(t)

for thread in threadlist:
    thread.join()

print(x)


stat = ''

while stat != 'q':
    insta_id = input('\nEnter the instance ID(enter q to exit): ')
    if insta_id == 'q':
        sys.exit(0)
    elif insta_list.get(insta_id) is None:
        print('Invalid instance Id\n')
        continue
    region = insta_list[insta_id]['Region']

    print('Select your Action: \n 1 - Start\n 2 - Stop\n 3 - Reboot\n 4 - Terminate\n q - Exit')
    stat = input('Enter your choice (1/2/3/4/q): ')

    if stat == '1':
        if insta_list[insta_id]['state'] == 'stopped':
            print('Starting instance\n')
            startinsta(insta_id, region)
        else:
            print('Invalid option: Instance state is: {}'.format(insta_list[insta_id]['state']))
    elif stat == '2':
        if insta_list[insta_id]['state'] == 'running':
            print('Stopping instance\n')
            stopinsta(insta_id, region)
        else:
            print('Invalid option: Instance state is: {}'.format(insta_list[insta_id]['state']))
    elif stat == '3':
        if insta_list[insta_id]['state'] == 'running':
            print('Rebooting instance\n')
            rebootinsta(insta_id, region)
        else:
            print('Invalid option: Instance state is: {}'.format(insta_list[insta_id]['state']))
    elif stat == '4':
        if insta_list[insta_id]['state'] != 'terminated':
            print('Terminating the instance\n')
            terminateinsta(insta_id, region)
        else:
            print('Invalid option: Instance state is: {}'.format(insta_list[insta_id]['state']))
    elif stat == 'q':
        print('Exiting')
        sys.exit(0)
    else:
        print('Invalid input\n')
