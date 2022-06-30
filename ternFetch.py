#!/usr/bin/env python3

# Import the standard python library
import subprocess
import argparse
import os
from sys import stdout
import dateutil.parser
from datetime import datetime,timedelta
import json
import arrow
from builtins import str
import re

# Create the parser
parser = argparse.ArgumentParser(
    description="tern_fetch_.py: Compute the Tern file for a repository"
)

# Add an argument
parser.add_argument(
    "--project", "-p", dest="project_name", help="Name of the project.  Required."
)
parser.add_argument(
    "--repo",
    "-r",
    dest="repo_name",
    required=True,
    help="Name of the repository.  Required.",
)
parser.add_argument(
    "--tag", "-t", dest="tag_name", required=True, help="Name of the tag"
)
parser.add_argument(
    "--push-time", "-d", dest="push_time", help="Perform scan on artifacts pushed to Harbor in last __ days", type=int
)
parser.add_argument(
    "--output-dir", "-o", dest="output_dir", help="Output directory for the Tern file"
)
parser.add_argument(
    "--verbose", "-v", action="store_true", dest="verbose", help="Verbose debugging"
)

# Parse the arguments
args = parser.parse_args()

# Use args to define repo:tag then format output
image_registry = "system.registry.aws-us-east-2.devstar.cloud/"
image = image_registry + args.project_name + "/" + args.repo_name + ":" + args.tag_name
#print(image)
newformat = image.replace(":", "-").replace("/", "-")

# print('Hello,', args)
#Check the push_time of the artifact
#print(cmnd)
#os.system(cmnd)

if args.push_time is not None:
    arw = arrow.utcnow()
    print(args.push_time, "days ago the date was",  arw.shift(days=-args.push_time), "Checking for pushes occuring since then.")
    #print(push_time)
    cmnd = 'curl -X GET https://$REGISTRY_URL/api/v2.0/projects/' + args.project_name + '/repositories/' + args.repo_name + '/artifacts?page=%d&page_size=40'  
    cmnd_response = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True) # returns the exit code
    #cmnd_response = subprocess.Popen([cmnd], capture_output=True) # returns the exit code with no shell
    stdout, stderr = cmnd_response.communicate()
    encoding = 'utf-8'
    #harbor_push_time = stdout.encode()
    decoded_harbor_push_time = stdout.decode(encoding)
    print(decoded_harbor_push_time)
    
    #print('**********data var below*****************')
    #print(type(decoded_harbor_push_time))
    
    #get the repo level push_time value
    parsed_push_time = decoded_harbor_push_time.split('\"push_time\"')
    

    print('******decoded to str below*****')
    print(parsed_push_time)


    print('***decoded registry push count below******')
    print(decoded_harbor_push_time.count('push_time'))

    print('***values from push_count below******')
    all_push_times = re.findall("push_time", decoded_harbor_push_time)
    print(all_push_times)

""" cmnd = (
    'sudo /mnt/c/projects/tern/docker_run.sh ternd "report -i %s -y 1" > /tmp/%s.txt'
    % (image, newformat)
) """
