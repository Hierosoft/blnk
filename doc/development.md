# Development

## Detecting the Mimetype
The goal is to add a new mimetype, not reuse one that the OS may try to
associate with other applications (on platforms that detect mimetype
from characteristics other than the file extension--See
"Why not use Desktop Entry").

### Why not use Desktop Entry
Adding the `[Desktop Entry]` section makes kmimetypefinder detect the
file as `application/x-desktop`, but that would prevent blnk from
doing fancy things like expanding cross-platofrm environment variables.

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


## Copypasta
```
grep "Encoding" -n -r /home/owner/.local/share/applications
```
