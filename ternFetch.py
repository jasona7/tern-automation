#!/usr/bin/env python3

# Import the standard python library
import argparse
import subprocess
import os

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
    "--update-time", "-u", dest="update_time", help="Update time of the repo"
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
print(image)
newformat = image.replace(":", "-").replace("/", "-")
# subprocess.Popen(["sudo", "/mnt/c/projects/tern/docker_run.sh", "ternd", "report", "-i", $image, "-y", "1"])
# print('Hello,', args)
cmnd = (
    'sudo /mnt/c/projects/tern/docker_run.sh ternd "report -i %s -y 1" > /tmp/%s.txt'
    % (image, newformat)
)
print(cmnd)
os.system(cmnd)