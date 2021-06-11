#!/bin/bash

rm *-light.svg

for file in *.svg; do

  fname=$(basename $file .svg)
  sed 's/currentColor/white/g' $file > "$fname-light.svg"

done
