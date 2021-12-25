#!/bin/bash
set -e

test ! -f "$1" && exit 1
test ! -r "$1" && exit 2

for ((;;)); do
    clear
    tail -n 25 "$1"
    sleep 2
done

exit 0
