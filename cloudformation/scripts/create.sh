#!/bin/bash
cd "$(dirname "$0")"

if [[ $# -eq 0 ]] ; then
    echo 'Please Provide Stack Name as First Argument.'
    exit 1
fi

aws cloudformation create-stack --profile labramp-dev --stack-name $1 --template-body "file://$PWD/../stacks/$1.yml"
