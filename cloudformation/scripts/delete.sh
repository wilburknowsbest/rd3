#!/bin/bash
cd "$(dirname "$0")"

aws cloudformation delete-stack --profile labramp-dev --stack-name cf-test
