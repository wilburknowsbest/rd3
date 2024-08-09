#!/bin/bash

cd "$(dirname "$0")/../../.."


docker compose run --rm --service-ports --name api.piccolo api