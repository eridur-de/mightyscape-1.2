#!/bin/bash

echo "Upgrading pip ..."
venv/bin/pip install pip --upgrade

echo "Upgrading dependencies ..."
#cat requirements.txt | sed '/^#/d' | xargs -n 1 venv/bin/pip install --upgrade --quiet --no-cache-dir
cat requirements.txt | sed '/^#/d' | xargs -n 1 venv/bin/pip install --upgrade --no-cache-dir
