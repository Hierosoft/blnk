# Development

## Detecting the Mimetype
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
