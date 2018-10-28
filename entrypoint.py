#!/usr/bin/env python3

import sys
import glob
import json
import subprocess
import cfnlint.decode.cfn_yaml as cfn_yaml

def is_cfn(filename):
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
    return [name.replace("%s/"%basedir, "", 1) for name in glob.iglob('%s/**/*'%basedir, recursive=True)]

def codacy_result(hit, path):
  return dict(filename=path,
              message=hit["Message"],
              patternId=hit["Rule"]["Id"],
              line=hit["Location"]["Start"]["LineNumber"])

def run_cfnlint(basedir, path, patterns):
    try:
        process = subprocess.run(["cfn-lint", "-f", "json", "%s/%s"%(basedir, path)], capture_output=True)
        hits = json.loads(process.stdout.decode('utf-8'))
        return [codacy_result(hit, path) for hit in hits if not patterns or hit["Rule"]["Id"] in patterns]
    except:
        return [dict(filename=path, message="could not parse the file")]


if __name__ == "__main__":
    basedir = "./src"
    files, patterns = parse_codacy_conf("%s/.codacy.json"%basedir)

    if not files:
        files = get_all_files(basedir)

    for path in files:
        if is_cfn("%s/%s"%(basedir, path)):
            for hit in run_cfnlint(basedir, path, patterns):
                print(json.dumps(hit))
