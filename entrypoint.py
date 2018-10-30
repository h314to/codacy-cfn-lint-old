#!/usr/bin/env python3

import os
import sys
import glob
import json
import subprocess
import cfnlint.decode.cfn_yaml as cfn_yaml

def is_cfn(filename):
    """Check if a file is a cloudformation template

    :param filename: name of the file to check
    :return        : True if it is, False otherwise
    """
    try:
        cfn = cfn_yaml.load(filename)
        if 'Resources' in cfn:
            return True
        else:
            with open(filename) as f:
                cfn = json.load(f)
            if 'Resources' in cfn:
                return True
            else:
                return False
    except:
        return False

def parse_codacy_conf(filename, toolname="cfn-lint"):
    """Try to load codacy.json file

    If the file is missing return two empty lists, otherwise,
    if the file exist and has files and/or patterns return those.

    :param filename: name of the file to parse (typically /.codacyrc)
    :param toolname: name of the tool, used to get patterns from the codacy.json file
    :return        : list of files, list of patterns to check
    """
    try:
        with open(filename) as f:
            codacyrc = json.load(f)
        
            if "files" in codacyrc:
                files = codacyrc["files"]
            else:
                files = list()
        
            patterns = list()
            for tool in codacyrc["tools"]:
                if tool["name"] == toolname:
                    patterns = [pattern["patternId"] for pattern in tool["patterns"]]
        return files, patterns

    except:
        return list(), list()

def get_all_files(basedir):
    """Get a list of all files in basedir, recursively

    :param basedir: base of the path where to look for the files
    :return       : a list with all the file paths
    """
    return [name.replace("%s/"%basedir, "", 1) for name in glob.iglob('%s/**/*'%basedir, recursive=True)]

def codacy_result(hit, path):
    """Convert a hit to the Codacy result format

    :param hit : a cfn-lint hit in json format
    :param path: the path of the file where the hit occured
    :return    : dictionary conforming to the Codacy format
    """
    return dict(filename=path,
              message=hit["Message"],
              patternId=hit["Rule"]["Id"],
              line=hit["Location"]["Start"]["LineNumber"])

def run_cfnlint(basedir, path, patterns):
    """Run cfn-lint on for a given file

    Run cfn-lint for a file using a subprocess, and return the results (in codacy format) for this file.

    :param basedir : base dir where the source files are located (e.g. /src)
    :param path    : path of the file to check (without the basedir)
    :param patterns: patterns to check for
    :return        : List of results in Codacy format, or a Codacy error message if there is an error
    """

    debug = True if (os.environ.get('DEBUG') and os.environ.get('DEBUG').lower().strip() == "true") else False
    cmd = (["cfn-lint", "-d", "-f", "json", "%s/%s"%(basedir, path)] if debug
            else ["cfn-lint", "-f", "json", "%s/%s"%(basedir, path)])

    try:
        process = subprocess.run(cmd, capture_output=True)
        hits = json.loads(process.stdout.decode('utf-8'))
        return [codacy_result(hit, path) for hit in hits if not patterns or hit["Rule"]["Id"] in patterns]
    except:
        return [dict(filename=path, message="could not parse the file")]


if __name__ == "__main__":
    try:
        basedir = "/src"
        files, patterns = parse_codacy_conf("/.codacyrc")

        # if .codacyrc has no files then check all
        if not files:
            files = get_all_files(basedir)

        for path in files:
            if is_cfn("%s/%s"%(basedir, path)):
                for hit in run_cfnlint(basedir, path, patterns):
                    print(json.dumps(hit))
    except Exception as e:
        print("Unknown error in tool:\n%s"%str(e))
        sys.exit(1)
