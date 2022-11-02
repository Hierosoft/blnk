#!/bin/sh
if [ "x$PREFIX" = "x" ]; then
    PREFIX="/usr/local"
fi
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
in_file="org.poikilos-blnk.mimetype"
if [ ! -f "$in_file" ]; then
    >&2 echo "Error: '$in_file' is missing. This script must run from the cloned blnk repo."
    exit 1
fi

EXPECTED_TYPE="`cat $in_file | grep mime-type | head -n1 | cut -d'=' -f2 | cut -d'"' -f2`"
if [ "x$EXPECTED_TYPE" = "x" ]; then
    # If not found, revert to the last known correct value.
    EXPECTED_TYPE="application/x-blnk"
fi

if [ "x$1" = "x--help" ]; then
    >&2 echo
    >&2 echo $0
    >&2 echo "---------------------"
    >&2 echo "This script installs the mimetype file \"$in_file\" for files ending in \".blnk\" so that you can register \"$EXPECTED_TYPE\" (rather than \"text/plain\", which blnk tries to handle as a fallback) with blnk."
    >&2 echo "Set PREFIX in the environment if desired. The default is /usr/local."
    >&2 echo "Set RUNAS_CMD in the environment if desired. The default is sudo. Set it to ' ' to prevent this and run as a non-root user."
    >&2 echo
    exit 0
fi

unexpected_db="/usr/share/mime"
expected_db="$PREFIX/share/mime"
unexpected_dest="$unexpected_db/packages/$in_file"
expected_dest="$expected_db/packages/$in_file"
if [ -f "$unexpected_dest" ]; then
    >&2 echo "Error: 'There is already a packaged version of $in_file at $unexpected_dest, so nothing will be done. If you are sure the package is removed, delete the file and this script will attempt to install it at the unpackaged location $expected_dest."
    exit 2
fi

if [ -f "$expected_dest" ]; then
    >&2 echo "* trying to update existing $expected_dest...uninstalling..."
    $RUNAS_CMD xdg-mime uninstall --mode system $expected_dest
    code=$?
    if [ $code -eq 0 ]; then
        >&2 echo "  Success"
    else
        >&2 echo "  Error: '$RUNAS_CMD xdg-mime uninstall --mode system $expected_dest' failed with error code $code."
        exit $code
    fi
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

cat <<END
Done


You can test the outcome by running
  mimetype \$file
where \$file is an existing filename ending in .blnk.

* testing mimetype...
END

TEST_BLNK="tests/data/test.blnk"
GOT_TYPE=`mimetype $TEST_BLNK | cut -d' ' -f2`
if [ "x$GOT_TYPE" != "x$EXPECTED_TYPE" ]; then
    echo "  Error: The command says \"$GOT_TYPE\" but the expected type for $TEST_BLNK is \"$EXPECTED_TYPE\"."
else
    echo "  Success ('mimetype $TEST_BLNK' says \"$GOT_TYPE\")"
fi

echo "* testing xdg-mime query filetype..."
XDG_GOT_TYPE="`xdg-mime query filetype $TEST_BLNK`"
if [ "x$XDG_GOT_TYPE" != "x$EXPECTED_TYPE" ]; then
    echo "  Error: The command says \"$XDG_GOT_TYPE\" but the expected type for $TEST_BLNK is \"$EXPECTED_TYPE\"."
else
    echo "  Success ('mimetype $TEST_BLNK' says \"$GOT_TYPE\")"
fi
