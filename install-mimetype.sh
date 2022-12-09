#!/bin/sh
>&2 cat <<END


$0
---------------------
END
NOEXIT=false

if [ "x$1" = "x--no-exit" ]; then
    NOEXIT=true
fi


exit_if(){
    # This is useless since it doesn't stop the script itself.
    code=$1
    if [ "x$code" = "x" ]; then
        code=1
    fi
    if [ "x$NOEXIT" = "xfalse" ]; then
        exit $code
    else
        return $code
    fi
}

. ./mimetype.rc
if [ "x$RUNAS_CMD" = "x" ]; then
    RUNAS_CMD="sudo"
fi
if [ "$RUNAS_CMD" = " " ]; then
    RUNAS_CMD=""
fi
if [ ! -f "`command -v $RUNAS_CMD`" ]; then
    echo "* $RUNAS_CMD doesn't exist, so it will not be used."
    RUNAS_CMD=""
fi

if [ ! -f "$in_file" ]; then
    # defined by mimetype.rc
    >&2 echo "Error: '$in_file' is missing. This script must run from the cloned blnk repo."
    exit 1
fi

EXPECTED_TYPE="`cat $in_file | grep mime-type | head -n1 | cut -d'=' -f2 | cut -d'"' -f2`"
if [ "x$EXPECTED_TYPE" = "x" ]; then
    # If not found, revert to the last known correct value.
    EXPECTED_TYPE="application/x-blnk"
fi

if [ "x$1" = "x--help" ]; then
    >&2 cat <<END
This script installs the mimetype file "$in_file" for files ending in ".blnk" so that you can register "$EXPECTED_TYPE" (rather than "text/plain", which blnk tries to handle as a fallback) with blnk.
Set PREFIX in the environment if desired. The default is /usr/local.
Set RUNAS_CMD in the environment if desired. The default is sudo. Set it to ' ' to prevent that default from being used and to run as the current user.

END
    exit 0
fi

. ./mimetype.rc
if [ $? -ne 0 ]; then exit 1; fi

if [ -f "$unexpected_dest" ]; then
    >&2 echo "Error: 'There is already a packaged version of $in_file at $unexpected_dest, so nothing will be done. If you are sure the package is removed, delete the file and this script will attempt to install it at the unpackaged location $expected_dest."
    exit 2
fi

echo "[$0] expected_db=$expected_db"
echo "[$0] unexpected_db=$unexpected_db"
if [ -f "$expected_dest" ]; then
    DONE_DEST="$expected_dest"
    >&2 echo "* trying to update existing $expected_dest..."
    >&2 echo "  uninstalling..."
    $RUNAS_CMD xdg-mime uninstall --mode system $expected_dest
    code=$?
    if [ $code -eq 0 ]; then
        >&2 echo "  Success"
        DONE_DEST="$expected_dest"
    else
        >&2 echo "  Error: '$RUNAS_CMD xdg-mime uninstall --mode system $expected_dest' failed with error code $code."
        exit $code
    fi
fi
if [ -f "$expected_dest" ]; then
    >&2 echo "Warning: The destination exists: $expected_dest"
    # xdg-mime uninstall should have removed it.
fi
echo "* installing $in_file..."
$RUNAS_CMD xdg-mime install --mode system $in_file
code=$?
if [ $code -eq 0 ]; then
    >&2 echo "  Success"
else
    >&2 echo "  Error: '$RUNAS_CMD xdg-mime install --mode system $in_file' failed with error code $code."
    exit $code
fi

if [ -f "$unexpected_dest" ]; then
    # This destination is not expected, but if it is here, try it.
    echo "* $unexpected_dest was installed."
    echo "* update-mime-database $unexpected_db"
    $RUNAS_CMD update-mime-database $unexpected_db
    code=$?
elif [ -f "$expected_dest" ]; then
    echo "* $expected_dest was successfully installed."
    echo "* update-mime-database $expected_db"
    $RUNAS_CMD update-mime-database $expected_db
    code=$?
else
    echo "Warning: After xdg-mime install, the file doesn't appear as $expected_dest, but '$RUNAS_CMD update-mime-database $expected_db' will be attempted anyway."
    $RUNAS_CMD update-mime-database $expected_db
    code=$?
fi

code=$?
if [ $code -eq 0 ]; then
    >&2 echo "  Success"
else
    >&2 echo "  Error: xdg-mime failed with error code $code."
    exit $code
fi


echo "* update-desktop-database"
$RUNAS_CMD update-desktop-database
code=$?
if [ $code -eq 0 ]; then
    >&2 echo "  Success"
else
    >&2 echo "  Error: update-desktop-database failed with error code $code."
    exit $code
fi


TEST_BLNK="tests/data/test.blnk"

>&2 echo "* testing 'mimetype $TEST_BLNK'..."

GOT_TYPE=`mimetype $TEST_BLNK | cut -d' ' -f2`
if [ "x$GOT_TYPE" != "x$EXPECTED_TYPE" ]; then
    echo "  Error: The command says \"$GOT_TYPE\" but the expected type for $TEST_BLNK is \"$EXPECTED_TYPE\"."
else
    echo "  Success ('mimetype $TEST_BLNK' says \"$GOT_TYPE\")"
fi

echo "* testing 'xdg-mime query filetype $TEST_BLNK'..."
XDG_GOT_TYPE="`xdg-mime query filetype $TEST_BLNK`"
if [ "x$XDG_GOT_TYPE" != "x$EXPECTED_TYPE" ]; then
    echo "  Error: The command says \"$XDG_GOT_TYPE\" but the expected type for $TEST_BLNK is \"$EXPECTED_TYPE\"."
else
    echo "  Success ('mimetype $TEST_BLNK' says \"$GOT_TYPE\")"
fi
