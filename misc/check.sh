#!/bin/bash

cd $1/default/replay
cp ../../../base/default/replay/check.txt check1.txt
cp ../../../base/default/replay/exec_times.txt exec_times1.txt
cmp check.txt check1.txt
cmp exec_times.txt exec_times1.txt
cmp -l check.txt check1.txt > temp.txt
