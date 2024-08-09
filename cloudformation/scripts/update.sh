#!/bin/bash
cd "$(dirname "$0")"

aws cloudformation update-stack --profile labramp-dev --stack-name cf-test --template-body "file://$PWD/../templates/cf-test.yml"
