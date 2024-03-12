#!/bin/bash

dd if=$1/default/replay/check.txt bs="$2" count=1 | wc -l
