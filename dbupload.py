#!/usr/bin/python

import dropbox
import argparse
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read('dbkeys.txt')

db_app_key = config.get('DropBoxKeys', 'db_app_key')
db_app_secret = config.get('DropBoxKeys', 'db_app_secret')
db_access_token = config.get('DropBoxKeys', 'db_access_token')

parser = argparse.ArgumentParser(description='files to upload')
parser.add_argument('-f','--file', help='Input file name',required=True)
args = parser.parse_args()

flow = dropbox.client.DropboxOAuth2FlowNoRedirect(db_app_key, db_app_secret)

client = dropbox.client.DropboxClient(db_access_token)

f = open(args.file)
response = client.put_file(args.file, f)
print "uploaded: ", response

