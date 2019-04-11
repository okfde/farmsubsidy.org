#!/bin/bash

set -ex

for file in $1/*.gz
do
echo $file && curl -v -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' -H 'Content-Encoding: gzip' --data-binary "@$file" ; echo $file
done
