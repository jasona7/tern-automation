# tern-automation

userdata.sh - Script for tern image scanning automation for EC2 bootstrap process.

ternFetch.py - Argument driven .py script targets a project, repo, and tag for Tern image scan

usage: ternFetch.py [-h] [--project PROJECT_NAME] --repo REPO_NAME --tag TAG_NAME [--update-time UPDATE_TIME] [--output-dir OUTPUT_DIR] [--verbose]

tern_fetch_.py: Compute the Tern file for a repository

optional arguments:
  -h, --help            show this help message and exit
  --project PROJECT_NAME, -p PROJECT_NAME
                        Name of the project. Required.
  --repo REPO_NAME, -r REPO_NAME
                        Name of the repository. Required.
  --tag TAG_NAME, -t TAG_NAME
                        Name of the tag
  --update-time UPDATE_TIME, -u UPDATE_TIME
                        Update time of the repo
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Output directory for the Tern file
  --verbose, -v         Verbose debugging
