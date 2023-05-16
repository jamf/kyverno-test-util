import sys
import yaml
import os
from types import NoneType

# ReplicaSet is not here, because I have no idea how to change policies to make it work
allowedResources = ['Job', 'Deployment', 'StatefulSet']
ignoredFileNames = ['prometheus-scrapeConfig', 'chart', 'Chart',
                    'values', 'CustomResourceDefinition', 'crds']

kyvernoTestFileName = 'kyverno-test.yaml'

def deleteLeftovers():
    if os.path.exists(kyvernoTestFileName):
        os.remove(kyvernoTestFileName)

def writeTitle():
    title = {'name': 'Kyverno test'}
    appendToFile(title)

def writePolicies(policies_location):
    policies = {'policies': [f'{policies_location}']}
    appendToFile(policies)

def getResourceLocations(folder):
    """
    Get's a list of resources that should be validated against policies.
    """
    resources = list()

    for root, dirs, files in os.walk(f'{folder}'):
        for file in files:
            if (file.endswith(".yaml") or file.endswith(".yml")) and ("kyverno" not in root) and len([ignored for ignored in ignoredFileNames if (file.find(ignored) != -1)]) == 0:
                resources.append(os.path.join(root, file))
    return resources

def writeResources(folder):
    resources = {'resources': getResourceLocations(folder)}
    appendToFile(resources)

def writeResults(folder, policies_location):
    results = {'results': getPreparedResults(folder, policies_location)}
    appendToFile(results)

def getExpectedResult(rule, resource):
    """
    This method is meant to determine what should be the result of given test.
    We don't have tests that are meant to fail, only pass, or if resource is to be ignored - skip.
    """
    shouldExclude = 0
    if 'exclude' in rule.keys():
        if 'namespace' in str(rule['exclude']) and resource['metadata']['namespace'] in rule['exclude']['any'][0]['resources']['namespaces']:
            shouldExclude = 1

        if 'kinds' in str(rule['exclude']) and resource['metadata']['name'] in rule['exclude']['any'][0]['resources']['names']:
            shouldExclude = 1

    if 'mutate' in rule.keys():
        shouldExclude = 1

    match shouldExclude:
        case 0:
            return 'pass'
        case 1:
            return 'skip'

def getResult(policy, rule, resource):
    result = dict()
    if resource['kind'] in allowedResources:
        result = {
            'policy': policy['metadata']['name'],
            'rule': rule['name'],
            'resources': [resource['metadata']['name']],
            'result': getExpectedResult(rule, resource),
            'kind': resource['kind']
        }

        if 'namespace' in resource['metadata'].keys():
            result['namespace'] = resource['metadata']['namespace']

    return result

def getPreparedResults(folder, policies_location):
    """
    Because there are multiple exclusions in policies and resources can have multiple objects in one file,
    this method iterates over everyting and strives to build `result` element for every available policy rule - resource combination
    """
    resourceLocations = getResourceLocations(folder)
    results = list()
    with open(policies_location) as policyFile:
        policies = yaml.safe_load_all(policyFile)
        for policy in policies:
            for rule in policy['spec']['rules']:
                for resource in resourceLocations:
                    with open(resource) as file:
                        resources = yaml.safe_load_all(file)
                        for resource in resources:
                            if type(resource) is dict:
                                result = getResult(policy, rule, resource)
                            else:
                                for obj in resource:
                                    result = getResult(policy, rule, obj)

                            if type(result) is not NoneType and len(result) > 0:
                                results.append(result)

    return results

def appendToFile(text):
    with open(kyvernoTestFileName, 'a') as testFile:
        yaml.safe_dump(text, testFile, default_flow_style=False)

def main():

    if len(sys.argv) != 3:
        print(f'Incorrect command. Should be `{sys.argv[0]} <folder_to_test> <path_to_policies_yaml>`')
        exit(1)
    elif not os.path.exists(sys.argv[1]):
        print(f'Folder {sys.argv[1]} does not exist')
        exit(1)
    elif not os.path.exists(sys.argv[2]):
        print(f'Policies file {sys.argv[2]} does not exist')
        exit(1)

    resources_folder = sys.argv[1]
    policies_location = sys.argv[2]

    deleteLeftovers()
    writeTitle()
    writePolicies(policies_location)
    writeResources(resources_folder)
    writeResults(resources_folder, policies_location)

if __name__ == "__main__":
    main()
