# blnk
https://github.com/poikilos/blnk
In a "blink," your program appears on any OS regardless of home folders parent directory location.

This is a Python rewrite of blnk-cs formerly called blnk (I didn't even look at the old code, only existing blnk files I had).

Cross-platform examples:
- "C:\Users\someone\Documents" becomes "~/Documents" on non-Windows systems but ~ is replaced with the actual user profile.
- "D:\Meshes" becomes "~/Nextcloud/Meshes", "~/ownCloud/Meshes", or "~/Meshes", whichever exists (first in that order).
- "C:\Users\someone\ownCloud" becomes "~/Nextcloud" or "~/ownCloud", whichever exists.

## Install
- Associate text files to blnk and it will try to edit the file if there is no Exec line (feature status: See `_choose_app` in blnk.py).

### On Linux
- Ensure you've installed `python3`
  - If necessary on your distro such as **Ubuntu**, install the `python-is-python3` package.
- Install `geany` to open text files if you associate text files with blnk due to not having a separate MIME type.
- Clone or extract the repository to `~/git/blnk` (if another location, change instances of that below) then:
```
mkdir -p ~/.local.bin
ln -s ~/git/blnk/blnk.py ~/.local/bin/blnk
```
- If `~/.local/bin` is not already in your path, add it to `~/.profile` so it works in both the graphical environment and terminals. Add the following line to `~/.profile`:
```
export PATH="$PATH:$HOME/.local/bin"
```

## Use
- Associate blnk files (or plain text files if you're ok with then opening in `geany`) with "blnk".
- Make a shortcut in the current directory to a path with `blnk -s` followed by a path.
  - This feature many replace filehandoff.
