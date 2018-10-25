#!/usr/bin/env python3

import os
import sys
import glob
import json
import importlib.util


def get_object(path, path_prefix):
        module_name = path.replace(path_prefix, "").replace(".py", "").replace("/", ".")
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        class_name = module_name.split(".")[-1]
        return getattr(module, class_name)

cfnlint_path = sys.argv[1]

os.makedirs("./docs/description", mode=0o755)
desc_file = open('./docs/tool-description.md', 'w')
desc_file.write("CloudFormation Linter is a tool to validate CloudFormation yaml/json")
desc_file.write("templates against the CloudFormation spec and additional checks.")
desc_file.write(" Includes checking valid values for resource properties and best practices.")
desc_file.write(" [Learn more](https://github.com/awslabs/cfn-python-lint)")

docs = list()
pats = dict(name="CloudFormationLinter", patterns=list())

level_map = dict(W="Warning", E="Error")

for path in glob.iglob("%s/src/cfnlint/rules/**/*.py"%cfnlint_path, recursive=True):
    if "__init__.py" not in path:
        obj = get_object(path, "%s/src/"%cfnlint_path)

        pats['patterns'].append(dict(patternId=obj.id,
                                     level=level_map[obj.id[0]],
                                     category="ErrorProne"))

        docs.append(dict(patternId=obj.id,
                         title=obj.shortdesc,
                         description=obj.__doc__,
                         timeToFix=5))

        rule_file = open("./docs/description/%s.md"%obj.id, 'w')
        rule_file.write("%s\n\n[SOURCE](%s)"%(obj.description, obj.source_url))

pats_file = open('./docs/patterns.json', 'w')
pats_file.write(json.dumps(pats, indent=4, sort_keys=True))

docs_file = open('./docs/description/description.json', 'w')
docs_file.write(json.dumps(docs, indent=4, sort_keys=True))
