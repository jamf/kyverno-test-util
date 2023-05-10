# Kyverno Test Util

A repository for python script that's meant to prepare test file for kyverno cli.  

## The problem

[Kyverno CLI](https://kyverno.io/docs/kyverno-cli/#test) delivers `test` command which allows users to perform policy validations against k8s resources.  
What it lacks is an ability to validate all resources from folder A against policies defined in folder B.  

## The solution

This script allows users to simply run

```bash
python kyverno-test-util.py <absolute_path_to_folder_with_k8s_resource_manifests> <absolute_path_to_file_with_policies>
```

Above command will produce `kyverno-test.yaml` file, which can then be used as an input to `kyverno test` command:

```bash
kyverno test ./kyverno-test.yaml
```
