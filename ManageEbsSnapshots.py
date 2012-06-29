#!/usr/bin/python
### ManageEbsSnapshots.py
### Written By: Carl Krauss
### Date: 5/18/2012
### Modified By: Okezie Eze
### Date: 06/23/2012
###Change Log:
#   0.2
###    Added OwnerID command line parameter which is used to retrieve only snapshots owned by the AWS customer identified by Owner ID.
###    Added error handling for all snapshot delete API calls
###    Changed date comparison operator in PurgeVolumeSnapshots() and PurgeOldSnapshots() 
###        from:
###            if Snapshot.start_time > PurgeDate.isoformat()
###        to:
###            if Snapshot.start_time < PurgeDate.isoformat()

from boto.ec2.connection import EC2Connection
import datetime 
#from dateutil.relativedelta import relativedelta
import sys
import argparse
import time

# Global Variables
version = '0.2'
description = 'Snapshot Created by ' + sys.argv[0] + ' at ' + datetime.datetime.today().isoformat(' ') + ' from VolumeID: '
#RunDate = datetime.datetime.today().isoformat()

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--AccessKey', action='store', dest='AccessKey', help='AWS Access Key', required=True)
parser.add_argument('-s', '--SecretKey', action='store', dest='SecretKey', help='AWS Secret Key', required=True)
parser.add_argument('-o', '--OwnerID', action='store', dest='OwnerID', help='AWS Secret Key', required=True)
parser.add_argument('-v', '--Volumes', action='store', dest='Volumes', help='Volume Id\'s Comma Seperated. At least one needed. "ALL" of all snapshots in Account')
parser.add_argument('-c', '--Create', action='store_true', dest='Create', help='Creates a Snapshot of the Volumes Passed.')
parser.add_argument('-p', '--PurgeDays', action='store', dest='PurgeDays', help='Purges everything older than the number specified. (Integer)', type=int)
parser.add_argument('-r', '--RemoveAfter', action='store_true', dest='RemoveAfter', help='Removes ALL Snapshots older than a set number of days. Use with --PurgeDays')
parser.add_argument('-n', '--Noop', action='store_true', dest='noop', help='No Opperation - Simulates Real Output')
#parser.add_argument('--version', action='version', version="%(prog)s %(version)s")
args = parser.parse_args()

AwsAccessKey = args.AccessKey
AwsSecretKey = args.SecretKey
Noop = args.noop
Create = args.Create
PurgeDays = args.PurgeDays
RemoveAfter = args.RemoveAfter
OwnerID = args.OwnerID

if args.Volumes is not None:
    Volumes = args.Volumes.split(",")
    # Checks to find out if only specific volumes require action
    if Volumes[0] == "ALL":
        AwsVolumes = conn.get_all_volumes()
    else:
        AwsVolumes = conn.get_all_volumes(Volumes)
else:
    Volumes = False;

conn = EC2Connection(AwsAccessKey, AwsSecretKey)



def CreateSnapshot(Volumes, Noop, description):
    for Volume in Volumes:
        if Noop:
            print ''
            print "Simulating Snapshot for Volume: " + str(Volume).split(":")[1] 
            SnapDescription = description + str(Volume).split(":")[1]
            print 'Snapshot created with description: ' + SnapDescription
        else:
            print ''
            print "Creating Snapshot for Volume: " + str(Volume).split(":")[1]
            SnapDescription = description + str(Volume).split(":")[1]
            if Volume.create_snapshot(SnapDescription):
                print 'Snapshot created with description: ' + SnapDescription
                #time.sleep(1) #Can remove if causing script to run too long. Stops hammering of AWS API

def PurgeVolumeSnapshots(Volumes, Noop, PurgeDays):
    PurgeDate = datetime.datetime.now() - datetime.timedelta(PurgeDays)
    for Volume in Volumes:
        Snapshots = Volume.snapshots()
        for Snapshot in Snapshots:
            if Noop:
                if Snapshot.start_time < PurgeDate.isoformat():
                    print 'Simulating Purge Snapshot for ' + str(Snapshot)
                #else:
                    #print str(Snapshot) + " is not ready to be purged."

            else:
                try:
                    if Snapshot.start_time < PurgeDate.isoformat():
                        print 'Purging Snapshot ' + str(Snapshot)
                        #Snapshot.delete()
                except:
                    print "Error deleting snapshot: ", sys.exc_info()[1]

def PurgeOldSnapshots(Snapshots, Noop, PurgeDays):
    PurgeDate = datetime.datetime.now() - datetime.timedelta(PurgeDays) 
    print "Removing all snapshots older than: ",str(PurgeDate.isoformat())
    for Snapshot in Snapshots:
        if Noop:
            if Snapshot.start_time < PurgeDate.isoformat():
                print 'Simulating Purge Snapshot for ' ,str(Snapshot),str(Snapshot.start_time)
            #else:
                #print str(Snapshot) + " is not ready to be purged."
                #print str(Snapshot.start_time) + " > " + str(PurgeDate.isoformat())
        else:
            try:
                if Snapshot.start_time < PurgeDate.isoformat():
                    print 'Purging Snapshot ',str(Snapshot),"CreatedDate:",str(Snapshot.start_time)
                    #print Snapshot.get_permissions()
                    Snapshot.delete()
                    
                #else:
                    #print str(Snapshot) + " is not ready to be purged."                      
            except:
                print "Error deleting snapshot: ",sys.exc_info()[1]
if Create and Volumes:
    CreateSnapshot(AwsVolumes,Noop,description)
elif Create:
    sys.exit('Please provide a Volume ID when using the --Create argument')
if PurgeDays and RemoveAfter:
    print "Retrieving all Snapshots..."
    AwsSnapshots = conn.get_all_snapshots(owner=OwnerID)
    PurgeOldSnapshots(AwsSnapshots,Noop,PurgeDays)
elif PurgeDays:
    PurgeVolumeSnapshots(AwsVolumes, Noop, PurgeDays)
elif RemoveAfter:
    sys.exit('Please provide the number of purge days with the --PurgeDays argument.')
