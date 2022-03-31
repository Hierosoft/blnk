# blnk
https://github.com/poikilos/blnk
In a "blink," your program appears on any OS regardless of home folders parent directory location.

This is a Python rewrite of blnk-cs formerly called blnk (I didn't even look at the old code, only existing blnk files I had).

## Features
- Automatically resolve cross-platform folder naming issues (such as if you are using a cloud app to sync files)! Cross-platform examples:
  - "C:\Users\someone\Documents" becomes "~/Documents" on non-Windows systems but ~ is replaced with the actual user profile.
  - "D:\Meshes" becomes "~/Nextcloud/Meshes", "~/ownCloud/Meshes", or "~/Meshes", whichever exists (first in that order).
  - "C:\Users\someone\ownCloud" becomes "~/Nextcloud" or "~/ownCloud", whichever exists.
- Automatically launch the correct program for files if the file isn't a blnk file, in case Linux detects the content type as text and you associate the file type with blnk.
  - The following extensions are known:
    - kdbx: keepassxc
    - nja: ninja-ide
  - The path ~/.local/bin is checked even if the matching program from the list above isn't in your PATH. That check resolves the issue of the feature only working from a terminal (such as if you added `PATH=$PATH:/home/owner/.local/bin` only to ~/.bashrc).
    - However, resolve the issue for yourself permanently using the step starting with "Add the local bin folder to your path for GUI applications" under "Install on Linux".

## Install
- Associate text files to blnk and it will try to edit the file if there is no Exec line (feature status: See `_choose_app` in blnk.py).

### Install on Linux
- Ensure you've installed `python3`
  - If necessary on your distro such as **Ubuntu**, install the `python-is-python3` package.
- Install `geany` to open text files if you associate text files with blnk due to not having a separate MIME type.
- Clone or extract the repository to `~/git/blnk` (if another location, change instances of that below and in the executable shell script `blnk`) then:
```
mkdir -p ~/.local.bin
ln -s ~/git/blnk/blnk ~/.local/bin/blnk
```
- Add the local bin folder to your path for GUI applications: If `~/.local/bin` is not already in your path, add it to `~/.profile` so it works in both the graphical environment and terminals. Add the following line to `~/.profile`:
```
export PATH="$PATH:$HOME/.local/bin"
```

### Enable logging
(on Linux)
- Install via `mkdir -p ~/git && git clone https://github.com/poikilos/blnk ~/git/blnk`
- Add `~/.local/bin` to your PATH then:
```
ln -s blnk ~/.local/bin/blnk
chmod +x ~/.local/bin/blnk
```


## Use
- Associate blnk files (or plain text files if you're ok with then opening in `geany`) with "blnk".
- Make a shortcut in the current directory to a path with `blnk -s` followed by a path.
  - This feature many replace filehandoff.

### Check logs
(requires that you first do the "Enable logging" steps and run blnk)
```
cat ~/.var/log/blnk/*
```

## Troubleshooting
Force automatic re-generation of icon on next run of blnk:
```
xdg-desktop-icon uninstall ~/.local/share/applications/blnk.desktop
xdg-desktop-icon uninstall ~/Desktop/blnk.desktop
rm ~/.local/share/applications/blnk.desktop
rm ~/Desktop/blnk.desktop
```

## Development
### Tasks
- [ ] Consider changing from ':' to '=' as per xdg shortcuts.

### Copypasta
```
grep "Encoding" -n -r /home/owner/.local/share/applications
```
