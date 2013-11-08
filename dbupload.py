#!/usr/bin/python

import dropbox
import argparse


db_app_key = 'uyvoyim1g8zr9nq'
db_app_secret = 'ymuz7cvfcpvkgad'
db_access_token = 'upVH_GCgW-0AAAAAAAAAAUL803vrMPm0IQYy309Wyc8uBUnmBhIZUY_tz8abLym5'

parser = argparse.ArgumentParser(description='files to upload')
parser.add_argument('-f','--file', help='Input file name',required=True)
args = parser.parse_args()

flow = dropbox.client.DropboxOAuth2FlowNoRedirect(db_app_key, db_app_secret)

client = dropbox.client.DropboxClient(db_access_token)

f = open(args.file)
response = client.put_file(args.file, f)
print "uploaded: ", response

