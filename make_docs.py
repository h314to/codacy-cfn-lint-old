#!/usr/bin/env python3

import os
import sys
import glob
import json
import importlib.util

# cfn-lint's source code is very well organized. Every rule is a class, and every class is systematically
# documented, for instance:
# 
# (...)
#   class Aliases(CloudFormationLintRule):
#       """Check if CloudFront Aliases are valid domain names"""
#       id = 'E3013'
#       shortdesc = 'CloudFront Aliases'
#       description = 'CloudFront aliases should contain valid domain names'
#       source_url = 'https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cloudfront-distribution-distributionconfig.html#cfn-cloudfront-distribution-distributionconfig-aliases'
#       tags = ['properties', 'cloudfront']
# (...)
# 
# Thus, in order to get the docs we can just find all source files, instantiate the class, and get its documentation.
# That is what this script, does do create patterns.json, description.json, and the markdown description for each rule.
# It further creates the ./docs folder and places everything in its right place.


def get_class_instance(path, path_prefix):
    """Get and instantiate class contained in a given souce file
    
    :param path        : source file containing a class we wish to instantiate
    :param path_prefix : prefix which sould be removed from the path to get the module name
    :return            : an instance of the class
    """
    module_name = path.replace(path_prefix, "").replace(".py", "").replace("/", ".")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    class_name = module_name.split(".")[-1]
    return getattr(module, class_name)


if len(sys.argv) != 2:
    print("usage: %s <cfn-lint source base dir>"%sys.argv[0])
    sys.exit(1)
else:
    cfnlint_path = sys.argv[1]

os.makedirs("./docs/description", mode=0o755)

desc_file = open('./docs/tool-description.md', 'w')
desc_file.write("CloudFormation Linter is a tool to validate CloudFormation yaml/json")
desc_file.write("templates against the CloudFormation spec and additional checks.")
desc_file.write(" Includes checking valid values for resource properties and best practices.")
desc_file.write(" [Learn more](https://github.com/awslabs/cfn-python-lint)")

docs = list()
pats = dict(name="cfn-lint", patterns=list())

LEVEL_MAP = dict(W="Warning", E="Error", I="Info")
CATEGORY_MAP = dict(W="CodeStyle", E="ErrorProne", I="Documentation")

for path in glob.iglob("%s/src/cfnlint/rules/**/*.py"%cfnlint_path, recursive=True):

    if path.split('/')[-1] == "__init__.py":
        continue

    print(path)
    rule_class = get_class_instance(path, "%s/src/"%cfnlint_path)

    pats['patterns'].append(dict(patternId=rule_class.id,
                                 level=LEVEL_MAP[rule_class.id[0]],
                                 category=CATEGORY_MAP[rule_class.id[0]]))

    docs.append(dict(patternId=rule_class.id,
                     title=rule_class.shortdesc,
                     description=rule_class.__doc__,
                     timeToFix=5))

    rule_file = open("./docs/description/%s.md"%rule_class.id, 'w')
    rule_file.write("%s\n\n[SOURCE](%s)"%(rule_class.description, rule_class.source_url))

pats_file = open('./docs/patterns.json', 'w')
pats_file.write(json.dumps(pats, indent=4, sort_keys=True))

docs_file = open('./docs/description/description.json', 'w')
docs_file.write(json.dumps(docs, indent=4, sort_keys=True))
