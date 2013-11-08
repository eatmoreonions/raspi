#!/usr/bin/python

import dropbox
import argparse


parser = argparse.ArgumentParser(description='files to upload')
parser.add_argument('-f','--file', help='Input file name',required=True)
args = parser.parse_args()

flow = dropbox.client.DropboxOAuth2FlowNoRedirect(db_app_key, db_app_secret)

client = dropbox.client.DropboxClient(db_access_token)

f = open(args.file)
response = client.put_file(args.file, f)
print "uploaded: ", response

