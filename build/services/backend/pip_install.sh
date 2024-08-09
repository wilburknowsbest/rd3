#!/bin/bash
WORK_DIR=/opt/service
cd $WORK_DIR

if [[ -s "$WORK_DIR"/shared/requirements.txt ]]; then
  pip install -r "$WORK_DIR"/shared/requirements.txt
fi

if [[ -s "$WORK_DIR"/requirements.txt ]]; then
  pip install -r "$WORK_DIR"/requirements.txt
fi
