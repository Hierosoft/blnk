#!/bin/sh
mkdir -p ~/.local/bin
logsDir=~/.var/log/blnk
mkdir -p "$logsDir"
if [ -z "$Exec" ]; then
    Exec=~/git/blnk/blnk/__init__.py
fi
>&2 echo "logsDir=$logsDir"
echo "Output:" > $logsDir/out.log
# >&2 echo "Errors:" > $logsDir/err.log
date >> $logsDir/out.log
# date >> $logsDir/err.log
python3 $Exec --non-interactive "$@" 1>>$logsDir/out.log 2>$logsDir/err.log
code=$?
>&2 echo >> $logsDir/out.log
# echo >> $logsDir/err.log
# cat $logsDir/err.log
cat $logsDir/out.log
if [ $code -ne 0 ]; then
    # TODO: If contains ModuleNotFoundError: No module named 'tkinter'
    #   then show a message saying:
    cat >/dev/null <<END
You have Python but not tkinter, so you must be on a Debian-based distro. First try: sudo apt-get install python3-tk
END
    err_line_count=`wc -l < $logsDir/err.log`
    >&2 cat "$logsDir/err.log"
    >&2 printf "Showing a GUI dialog box..."
    if [ $err_line_count -gt 0 ]; then
        xmessage -file "$logsDir/err.log"
        if [ $? -ne 0 ]; then
            >&2 echo "FAILED (xmessage didn't work. See the message below instead.)"
            >&2 echo
            >&2 cat "$logsDir/err.log"
        else
            >&2 echo "OK"
        fi
    else
        msg="Blnk had an unrecorded error. See $logsDir/out.log for information about the last run."
        xmessage "$msg"
        if [ $? -ne 0 ]; then
            >&2 echo "FAILED (xmessage didn't work. See the message below instead.)"
            >&2 echo
            >&2 echo "$msg"
        else
            >&2 echo "OK"
        fi
    fi
    exit $code
else
    err_line_count=`wc -l < "$logsDir/err.log"`
    if [ $err_line_count -gt 0 ]; then
        >&2 cat "$logsDir/err.log"
    fi
fi
