#!/bin/bash
cd "$(dirname "$0")"

if [[ $# -eq 0 ]] ; then
    echo 'Please Provide Stack Name as First Argument.'
    exit 1
fi

INCLUDE_EVENTS=false
while getopts "he" opt; do
  case $opt in
  h)  echo "use -e to include stack events" ;;
  e)  INCLUDE_EVENTS=true ;;
  \?)
    echo "Invalid option: -$OPTARG" >&2
    exit 1
    ;;
  esac
  shift
done

aws cloudformation describe-stacks --profile labramp-dev --stack-name $1

if $INCLUDE_EVENTS; then
    aws cloudformation describe-stack-events --profile labramp-dev --stack-name $1
fi
