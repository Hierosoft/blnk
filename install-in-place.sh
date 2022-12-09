#!/bin/bash
rel_exe="scripts/blnk"
if [ ! -f "$rel_exe" ]; then
    >&2 echo "$rel_exe is missing. This must run from the blnk repo."
    exit 1
fi
real_exe="`realpath $rel_exe`"
if [ "x$PREFIX" = "x" ]; then
    PREFIX=~/.local
fi
THIS_XDG_APP_ID=org.poikilos-blnk
OLD_NAME="org.poikilos.blnk.desktop"
SC_NAME="$THIS_XDG_APP_ID.desktop"
BIN_NAME="blnk"
DISPLAY_NAME="BLnk"
MIMETYPE="application/x-blnk"
APPLICATIONS=$PREFIX/share/applications
mkdir -p $APPLICATIONS

BIN_DIR=$PREFIX/local/bin
mkdir -p "$BIN_DIR"

BIN_FILE="$BIN_DIR/$BIN_NAME"
if [ -f "$BIN_FILE" ]; then
    >&2 printf "* removing old \"$BIN_FILE\"..."
    rm "$BIN_FILE"
    if [ $? -ne 0 ]; then
        >&2 echo "FAILED"
        exit 1
    else
        >&2 echo "OK"
    fi
fi

>&2 printf "* 'ln -s \"$real_exe\" \"$BIN_FILE\"'..."
ln -s "$real_exe" "$BIN_FILE"
if [ $? -ne 0 ]; then
    >&2 echo "FAILED"
    exit 1
else
    >&2 echo "OK"
fi

OLD_SC_FILE="$APPLICATIONS/$OLD_NAME"
SC_FILE="$APPLICATIONS/$SC_NAME"

if [ -f "$OLD_SC_FILE" ]; then
    >&2 echo "* removing deprecated \"$OLD_SC_FILE\""
fi

>&2 printf "* writing \"$SC_FILE\"..."
cat > "$SC_FILE" <<END
[Desktop Entry]
Exec=$BIN_FILE
MimeType=$MIMETYPE;
NoDisplay=false
Name=$DISPLAY_NAME
Type=Application
END
if [ $? -ne 0 ]; then
    >&2 echo "FAILED"
    exit 1
else
    >&2 echo "OK"
fi

./install-mimetype.sh

PREV_PREFIX="$PREFIX"

# mimetype.rc will use the environment's prefix if any, so blank it for now.
# FIXME: Set prefix to the one that install-mimetype used.
PREFIX=
source mimetype.rc
if [ $? -ne 0 ]; then exit 1; fi
if [ ! -f "$DONE_DEST" ]; then
    echo "Error: The mimetype file (DONE_DEST='$DONE_DEST') was not installed."
    exit 1
fi

PREFIX="$PREV_PREFIX"

THIS_XDG_DATA_DIR=$PREFIX/share
# MIMEAPPS_LIST=$THIS_XDG_DATA_DIR/applications/mimeapps.list
# ^ didn't work (doesn't show up in Open With menu--see
#   <https://forums.linuxmint.com/viewtopic.php?t=272852>:
MIMEAPPS_LIST=~/.config/mimeapps.list

>&2 printf "Adding $MIMETYPE=$SC_NAME to $MIMEAPPS_LIST..."
if [ ! -f $MIMEAPPS_LIST ]; then
    mkdir -p $PREFIX/share/applications
    echo "$MIMETYPE=$SC_NAME" > $MIMEAPPS_LIST
    if [ $? -ne 0 ]; then
        >&2 echo "FAILED"
        exit 1
    else
        >&2 echo "OK"
    fi

else
    if grep -Fxq "$MIMETYPE=$SC_NAME" $MIMEAPPS_LIST
    then
        >&2 echo "OK ($MIMETYPE=$SC_NAME was already in $MIMEAPPS_LIST)"
    else
        echo "$MIMETYPE=$SC_NAME" >> $MIMEAPPS_LIST
    fi
    if [ $? -ne 0 ]; then
        >&2 echo "FAILED"
        exit 1
    else
        >&2 echo "OK"
    fi
fi

# /dev/null since it doesn't seem to be necessary anymore (After switching to ~/.config/mimeapps.list above).
cat >/dev/null <<END

The following manual step may be necessary if $THIS_XDG_DATA_DIR is not in
(XDG_DATA_DIRS=$XDG_DATA_DIRS):
- Associate a .blnk file with blnk:
  Double click a blnk file, click "Choose a Program" button, choose blnk, check "Always use..."
  (If a different program was already set, right-click a .blnk file, Open With, choose blnk, check "Always use...").


END
