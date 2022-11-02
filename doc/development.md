# Development

## Mimetype
The goal is to add a new mimetype, not reuse one that the OS may try to
associate with other applications (on platforms that detect mimetype
from characteristics other than the file extension--See
"Why not use Desktop Entry").

The mimetype is application/x-blnk, formerly text/blnk. See
install-mimetype.sh and the `in_file=` line. The file that refers to is
the mimetype definition in xdg-mime's format. For futher examples, see
my other projects (under Poikilos on GitHub): b3view (fork),
ForwardFileSync, and filehandoff.


### Why not use Desktop Entry
Adding the `[Desktop Entry]` section makes kmimetypefinder detect the
file as `application/x-desktop`, but that would prevent blnk from
doing fancy things like expanding cross-platofrm environment variables.

Blnk has its own standard pending any suggested additions to
freedesktop.org's [Desktop Entry
Specification](https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#recognized-keys).
However, Blnk follows the standard as much as possible, and in the case
of extending it, follows the Desktop Entry Specification rule for
extending the Desktop Entry Specification (new features must be in a
section starting with "X-").

Important differences in Blnk:
- implements the proposed "Type=File" type.
- implements Path as the path storage key for a Directory or File
  (formerly Exec was used).
- must start with a line that is exactly "[X-Blnk]"
  (formerly starting with "Content-Type: text/blnk" or that followed
  by a semicolon).
  - doesn't start with "[Desktop Entry]" because that would make the
    mimetype application/x-desktop which is already handled by
    commands from xdg-utils or by software specific to the desktop
    environment.
- implements a new "[X-Target Metadata]" section to store the "created"
  and "modified" (or only "accessed" in the case of URLs) date(s) of
  the target file upon creating the shortcut.


#### WIP

##### Old format parts
If it starts with:
```
Content-Type: text/blnk
```
- `file --mime-type` and `kmimetypefinder` both identify it as `text/plain`.

If it starts with:

```
Content-Type: text/blnk
[Desktop Entry]
```
- `kmimetypefinder` says `application/x-desktop`.
- `file --mime-type` still says `text/plain`.


##### Copypasta
```
grep "Encoding" -n -r /home/owner/.local/share/applications
```
