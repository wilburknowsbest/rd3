#!/bin/bash
cd "$(dirname "$0")"

aws cloudformation describe-stacks --profile labramp-dev --stack-name cf-test
