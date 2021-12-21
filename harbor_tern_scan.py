#!/usr/bin/env python3
#
# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
#
# Security Response Tool Commandline Tool
#
# Copyright (C) 2021       Wind River Systems
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import sys
import argparse
import json
import subprocess
import time
import pytz
from datetime import datetime, date
import random

# Setup:
LOG_FILE = 'hb_test_dbg.log'
verbose = False
disable_fix = False

#################################
# Helper methods
#

# quick development/debugging support
log_fd = None
def _log_open():
    global log_fd
    log_fd=open('hb_test_dbg.log', 'a')

def _log(msg,also_print=False):
    global log_fd
    if also_print: print(msg)
    log_fd.write(msg+'\n' )

def _log_close():
    global log_fd
    log_fd.close()

# Sub Process calls
def execute_process(*args):
    cmd_list = []
    for arg in args:
        if not arg: continue
        if isinstance(arg, (list, tuple)):
            # Flatten all the way down
            for a in arg:
                if not a: continue
                cmd_list.append(a)
        else:
            cmd_list.append(arg)
    result = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode,result.stdout.decode('utf-8'),result.stderr.decode('utf-8')


histogram = {}
def histogram_add(seconds):
    global histogram
    if not seconds in histogram:
        histogram[seconds] = 1
    else:
        histogram[seconds] += 1

def histogram_print():
    global histogram
    _log("\nHistogram of API call time (in seconds):",True)
    for seconds in histogram:
        _log("%3d] %d" % (seconds,histogram[seconds]),True)

#################################
# Safe Curl call to Harbor, with timeout protection
#
# cmnd = ['curl','-X','GET','https://system.registry.aws-us-east-2.devstar.cloud/api/v2.0/projects?page=1&page_size=40','-H','accept: application/json','-H','X-Request-Id: 1234','-o',temp_file]
# e_stderr="curl: (7) Failed to connect to system.registry.aws-us-east-2.devstar.cloud port 443: Connection timed out"
#

import signal
from contextlib import contextmanager

@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after 'time', in seconds
    signal.alarm(time)
    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)

def raise_timeout(signum, frame):
    raise TimeoutError

def fetch_harbor(cmnd):
    _log('  * Try:%s' % ' '.join(cmnd))
    # Append curl timeout
    run_cmnd = cmnd + list(('--max-time','3'))
    datetime_start = datetime.now(pytz.utc)
    # Execute request, capture time spent
    e_returncode = 666
    e_stdout = "Error:timeout"
    e_stderr = "Error:timeout"
    if disable_fix:
        e_returncode,e_stdout,e_stderr = execute_process(cmnd)
    else:
        with timeout(5):
            e_returncode,e_stdout,e_stderr = execute_process(cmnd)
    seconds = (datetime.now(pytz.utc)-datetime_start).seconds
    if 666 == e_returncode:
        # First Timout Fail
        _log('=> ERROR_PYTHON_TIMEOUT_TRY1')
        # Try once more... (usually works immediately)
        with timeout(5):
            e_returncode,e_stdout,e_stderr = execute_process(cmnd)
    # Final disposition
    if 666 == e_returncode:
        # Second Timout Fail
        _log('=> ERROR_PYTHON_TIMEOUT_TRY2')
    elif e_returncode:
        _log('=> ERROR_CURL_TIMEOUT')
    elif seconds < 7:
        _log('   SUCCESS:%s seconds' % seconds)
    else:
        _log('=> SUCCESS:EXCCESSIVE_TIME=%s seconds' % seconds)
    histogram_add(seconds)
    return e_returncode,e_stdout,e_stderr,seconds

#################################
# load_products
#
temp_file = '_hb.json'

def load_hb_projects():
    count = 0
    page = 0
    loop = True

    object_list = []
    while loop:
        page += 1
        cmnd = ['curl','-X','GET','https://system.registry.aws-us-east-2.devstar.cloud/api/v2.0/projects?page=%d&page_size=40' % page,'-H','accept: application/json','-H','X-Request-Id: 1234','-o',temp_file]
        if verbose: print("Try:%s" % ' '.join(cmnd))
        e_returncode,e_stdout,e_stderr,seconds = fetch_harbor(cmnd)
        if e_returncode:
            print("ERROR:load_products:%s,%s,%s" % (e_returncode,e_stdout,e_stderr))
            return([])
        print("    Page %2s: %s" % (page,seconds))

        with open(temp_file) as json_data:
            dct = json.load(json_data)
            if not dct:
                loop = False
            else:
                object_count = 0
                for project in dct:
                    count += 1
                    object_count += 1
                    if verbose and datetime.strptime(project['update_time'], "%Y-%m-%dT%H:%M:%S:%SSZ") > datetime.now(pytz.utc) - 10:
                        print("PROJECT:%s" % project['name'])
                        print("     ID:%s" % project['project_id'])
                        print("  REPOS:%s" % (project['repo_count'] if 'repo_count' in project else 'N/A'))
                        print(" UPDATE:%s" % project['update_time'])
                    object_list.append(project['name'])
                if object_count < 40:
                    loop = False
    if verbose: print("Load Projects Count = %d" % count)
    return(object_list)

def load_hb_repos(project):
    page = 0
    loop = True
    count = 0

    object_list = []
    while loop:
        page += 1
        cmnd = ['curl','-X','GET','https://system.registry.aws-us-east-2.devstar.cloud/api/v2.0/projects/%s/repositories?page=%d&page_size=40' % (project,page),'-H','accept: application/json','-H','X-Request-Id: 1234','-o',temp_file]
        e_returncode,e_stdout,e_stderr,seconds = fetch_harbor(cmnd)
        if e_returncode:
            print("ERROR:LOAD_PRODUCTS:%s,%s,%s" % (e_returncode,e_stdout,e_stderr))
            return([])
        print("    Page %2s: %s" % (page,seconds))

        with open(temp_file) as json_data:
            dct = json.load(json_data)
            if not dct:
                loop = False
            else:
                object_count = 0
                for repo in dct:
                    count += 1
                    object_count += 1
                    if verbose:
                        print("[%3d] REPO:%s" % (count,repo['name']))
                        print("      PROJ:%s" % repo['project_id'])
                        print("        ID:%s" % repo['id'])
                        print("     PULLS:%s" % repo['pull_count'])
                        print("    UPDATE:%s" % repo['update_time'])

                    object_list.append(repo['name'])
                if object_count < 40:
                    loop = False
    if verbose: print("Load Repos Count = %d" % count)
    return(object_list)

def load_hb_artifacts(project,repo):
    page = 0
    loop = True
    count = 0

    repo_url = repo
#    repo_url = repo_url.replace('%s/' % project,'')
    repo_url = repo_url.replace('/','%2F')

    object_list = []
    while loop:
        page += 1

        # curl -X GET "https://system.registry.aws-us-east-2.devstar.cloud/api/v2.0/projects/wr-studio-product/repositories/wrlinux%2Frabbitmq/artifacts?page=1&page_size=10&with_tag=true&with_label=false&with_scan_overview=false&with_signature=false&with_immutable_status=false" -H  "accept: application/json"

        cmnd = ['curl','-X','GET','https://system.registry.aws-us-east-2.devstar.cloud/api/v2.0/projects/%s/repositories/%s/artifacts?page=%d&page_size=40' % (project,repo_url,page),'-H','accept: application/json','-H','X-Request-Id: 1234','-o',temp_file]
        e_returncode,e_stdout,e_stderr,seconds = fetch_harbor(cmnd)
        if e_returncode:
            print("ERROR:LOAD_PRODUCTS:%s,%s,%s" % (e_returncode,e_stdout,e_stderr))
            return([])
        print("    Page %2s: %s" % (page,seconds))

        with open(temp_file) as json_data:
            dct = json.load(json_data)
            if not dct:
                loop = False
            else:
                object_count = 0
                for artifact in dct:
                    count += 1
                    object_count += 1
                    if verbose:
                        print("[%3d] ARTIFACT:%s" % (count,artifact['digest']))
                        print("      REPO:%s" % artifact['repository_id'])
                        print("        ID:%s" % artifact['id'])
                    object_list.append(artifact['digest'])
                if object_count < 40:
                    loop = False
    if verbose: print("Load Artifacts Count = %d" % count)
    return(object_list)

""" def load_hb_vulnerabilities(repo_name,artifact_sha):
    page = 0
    loop = True
    count = 0
    datetime_now = datetime.now(pytz.utc)

    ####
    return([])

    print("    %s,%s" % (repo_name,artifact_sha))

    object_list = []
    while loop:
        page += 1 """

""" ####
#        'https://system.registry.aws-us-east-2.devstar.cloud/api/v2.0/projects/%s/repositories/%s/artifacts/%s/additions/vulnerabilities?page=%d&page_size=100' %
#            (project_name,repo_url,hb_artifact[ORM.WR_STUDIO_HARBORARTIFACT_NAME],page),


        # curl -X GET "https://system.registry.aws-us-east-2.devstar.cloud/api/v2.0/projects/wr-studio-product/repositories/wrlinux%2Frabbitmq/artifacts/sha256%3A3b944b1aed1abf1bcb685a84a590a8593d52c30f6fe37fd6bb2496becf384fd7/additions/vulnerabilities" -H  "accept: application/json" -H  "X-Request-Id: 1234"
        cmnd = ['curl','-X','GET','https://system.registry.aws-us-east-2.devstar.cloud/api/v2.0/projects/%s/repositories/%s/artifacts/%s/additions/vulnerabilities?page=%d&page_size=100' % (project_name,repo_url,hb_artifact_name,page),'-H','accept: application/json','-H','X-Request-Id: 1234','-o',temp_file]
        e_returncode,e_stdout,e_stderr,seconds = fetch_harbor(cmnd)
        if e_returncode:
            print("ERROR:LOAD_VULNERABILITY:%s,%s,%s" % (e_returncode,e_stdout,e_stderr))
            return([])
        print("    Page %2s: %s" % (page,seconds))

        with open(temp_file) as json_data:
            dct = json.load(json_data)
            if not dct:
                loop = False
            else:
                try:
                    scan = dct["application/vnd.scanner.adapter.vuln.report.harbor+json; version=1.0"]
                except Exception as e:
                    # dct={'errors': [{'code': 'NOT_FOUND', 'message': 'report not found for prodrigu/hello-artifact@sha256:7a5a2a1eae5f1708f29b41de0ccbfd890642a3ee7f27dd7eff28ea96ec05beb3'}]}
                    print("ERROR:scan:%s" % e)
                    print("      dct=%s" % dct)
                    exit(1)
                for vulnerability in scan['vulnerabilities']:
                    count += 1
                    if verbose:
                        print("[%3d] VUL:%s" % (count,vulnerability['id']))
                        print("  PACKAGE:%s" % vulnerability['package'])
                        print("       VER:%s" % vulnerability['version'])
                        print("    FIXVER:%s" % vulnerability['fix_version'])
                        print("       SEV:%s" % vulnerability['severity'])
                        print("      DESC:%s" % vulnerability['description'][0:20])
                    object_list.append(vulnerability['id'])

        # WARNING: the API for vulnerabilities does not implement the page syntax
        # so one pass is correct at this time
        loop = False

    print("Load Vulnerabilities Count = %d" % count)
    return(object_list) """

#################################
# Walk the Harbor tree
#

def main(argv):
    global verbose

#################################
# main loop
#

def hb_get_random(list_len):
    #print("get_random(%s)" % list_len)
    if list_len < 1:
        return 0
    else:
        return(random.randint(0, list_len - 1))

def main(argv):
    global verbose
    global disable_fix

    parser = argparse.ArgumentParser(description='srtool_wr.py: Manage SRTool to Wind River')
    parser.add_argument('--count', '-n', dest='count', help='Number of test calls to Harbor')
    parser.add_argument('--verbose', '-v', action='store_true', dest='verbose', help='Verbose debugging')
    parser.add_argument('--disable-fix', '-f', action='store_true', dest='disable_fix', help='Disable the workaround fix')
    args = parser.parse_args()

    verbose = args.verbose
    disable_fix = args.disable_fix
    count = 10
    if args.count:
        count = int(args.count)

    start_time = datetime.now()
    print("Start Time: %s" % start_time)

    # Run the test loops
    _log_open()
    projects = load_hb_projects()
    i = 0

    start_time = datetime.now()
    print("Start Time: %s" % start_time)
    print("Run  Count: %s" % count)
    while i < count:
        sys.stdout.flush()
        i += 1

        project_idx = hb_get_random(len(projects))
        project = projects[project_idx]
        print("%3d] : %s (%d/%d)" % (i,project,project_idx,len(projects)))
        repos = load_hb_repos(project)
        if 0 == len(repos):
            continue

        repo_idx = hb_get_random(len(repos))
        repo = repos[repo_idx]
        print("      %s (%d/%d)" % (repo,repo_idx,len(repos)-1))
        artifacts = load_hb_artifacts(project,repo)
        if 0 == len(artifacts):
            continue

        artifact_idx = hb_get_random(len(artifacts))
        artifact = artifacts[artifact_idx]
        print("      %s (%d/%d)" % (artifact,artifact_idx,len(artifacts)-1))
        #vulnerabilities = load_hb_vulnerabilities(repo,artifact)

    histogram_print()
    _log_close()
    stop_time = datetime.now()
    print("Stop Time: %s, (elapsed=%s)" % (stop_time, stop_time - start_time))
    print("Done.")

if __name__ == '__main__':
    main(sys.argv[1:])
