#!/bin/sh
command="sudo xdg-mime"
if [ ! -f "`command -v sudo`" ]; then
    command="xdg-mime"
fi
in_file="org.poikilos-blnk.mimetype"
if [ ! -f "$in_file" ]; then
    echo "Error: '$in_file' is missing. This script must run from the cloned blnk repo."
    exit 1
fi
$command install --mode system $in_file
code=$?
if [ $code -eq 0 ]; then
    >&2 echo "Success"
else
    >&2 echo "Error: '$command install --mode system $in_file' failed with error code $code."
fi
