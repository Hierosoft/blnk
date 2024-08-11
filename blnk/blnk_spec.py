'''
BLink Specification Metadata
----------------------------
by Jake Gustafson

This file provides defaults and requirements for creating .blnk files.

The blnk format is based on the XDG desktop shortcut format.
It uses the "X-" prefix for each section since it behaves differently
and according to XDG desktop file format:
- "X-" must start each section name that extends the format.

Also note that regarding XDG Format:
- "Encoding=UTF-8" is deprecated.

REQUIREMENTS and DEFAULTS:
- This should NOT have the MimeType key, which is used "to indicate the
  MIME Types that an application knows how to handle"
  -<https://specifications.freedesktop.org/desktop-entry-spec
  /desktop-entry-spec-latest.html>
- Each mostly has the same keys:
  - 'Exec': For making a File shortcut. formerly blnk.blnkTemplate
  - 'File' and "Directory": For making a File or Directory shortcut
    (formerly blnk.fileOrDirTemplate)
  - 'URL': For making a URL shortcut. formerly blnk.blnkURLTemplate
- REQUIREMENTS and DEFAULTS are not for blnk files, and not blnk itself.
  For installing a shortcut to blnk itself (required for easily setting
  it as the default program for the mimetype), see __init__.py (dtLines
  defines that file's format, which is strictly XDG desktop file
  format).

Soft requirements made hard (only for save, not load) in BLink class for
consistent operation:
Comment, modified, created, hostname, accessed
'''

import copy
from collections import OrderedDict

REQUIREMENTS = {}  # Values None (for easy copy), keys required
DEFAULTS = {}
for exec_type in ("Exec", "File", "Directory", "URL"):
    REQUIREMENTS[exec_type] = OrderedDict()
    REQUIREMENTS[exec_type]["X-Blnk"] = OrderedDict()
    REQUIREMENTS[exec_type]["X-Blnk"]["Type"] = None
    REQUIREMENTS[exec_type]["X-Blnk"]["Name"] = None
    REQUIREMENTS[exec_type]["X-Blnk"]["Comment"] = None
    REQUIREMENTS[exec_type]["X-Source Metadata"] = OrderedDict()
    REQUIREMENTS[exec_type]["X-Target Metadata"] = OrderedDict()
    REQUIREMENTS[exec_type]["X-Source Metadata"]["hostname"] = None

REQUIREMENTS["Exec"]["X-Blnk"]["Exec"] = None
REQUIREMENTS["Exec"]["X-Blnk"]["Terminal"] = None
REQUIREMENTS["Directory"]["X-Blnk"]["Path"] = None
REQUIREMENTS["File"]["X-Blnk"]["Path"] = None
REQUIREMENTS["URL"]["X-Blnk"]["URL"] = None

REQUIREMENTS["Exec"]["X-Target Metadata"]["created"] = None
REQUIREMENTS["Exec"]["X-Target Metadata"]["modified"] = None
REQUIREMENTS["Directory"]["X-Target Metadata"]["created"] = None
REQUIREMENTS["Directory"]["X-Target Metadata"]["modified"] = None
REQUIREMENTS["File"]["X-Target Metadata"]["created"] = None
REQUIREMENTS["File"]["X-Target Metadata"]["modified"] = None
REQUIREMENTS["URL"]["X-Target Metadata"]["accessed"] = None

for exec_type in ("Exec", "File", "Directory", "URL"):
    DEFAULTS[exec_type] = copy.deepcopy(REQUIREMENTS[exec_type])
    DEFAULTS[exec_type]["X-Blnk"]["NoDisplay"] = True

DEFAULTS["URL"]["X-Blnk"]["Icon"] = "folder-remote"

EXAMPLE_DATA = "```"
for section, meta in DEFAULTS["Exec"].items():
    EXAMPLE_DATA += "\n[{}]\n".format(section)
    for k, v in meta.items():
        readable_v = v
        if readable_v is None:
            readable_v = "{" + k + "}"
        elif readable_v is True:
            readable_v = "true"
        elif readable_v is False:
            readable_v = "false"
        EXAMPLE_DATA += "{}={}\n".format(k, readable_v)
EXAMPLE_DATA += "```"

TARGET_MAP = {
    "Exec": "Exec",
    "Directory": "Path",
    "File": "Path",
    "URL": "URL",
}