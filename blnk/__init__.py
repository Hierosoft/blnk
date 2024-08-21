# -*- coding: utf-8 -*-

# DOCSTRING: See __doc__ further down for documentation.

from __future__ import print_function

import argparse
import os
import pathlib
import platform
import shlex  # See shlex.join polyfill further down in case of Python 2
import socket
import subprocess
import sys

from collections import OrderedDict
from blnk.blnk_spec import (
    REQUIREMENTS,
    DEFAULTS,
    EXAMPLE_DATA,
    TARGET_MAP,
)

from blnk.find_hierosoft import hierosoft

import hierosoft.logging2 as logging
from hierosoft.logging2 import getLogger

logger = getLogger(__name__)
# logger.setLevel(logging.INFO)
# ^ Doesn't to anything! Instead do:
logging.basicConfig(level=logging.DEBUG)  # format='%(message)s'

if sys.version_info.major >= 3:
    # shlex_quote: See further down
    import datetime
    from datetime import timezone
    try:
        timezone_utc = timezone.utc
        # ^ "ModuleNotFoundError: No module named 'datetime.timezone';
        #   'datetime' is not a package"
    except ModuleNotFoundError:
        logger.error("sys.path={}".format(sys.path))
        logger.error(
            "sys.version_info={}".format(sys.version_info))
        raise
    try:
        import tkinter as tk
        # from tkinter import ttk
        from tkinter import messagebox
        # ENABLE_TK = True
        # ^ Check for it with `if 'tk' in globals():` instead.
        # - only tkinter is in sys.modules--`as` doesn't change that.
    except ModuleNotFoundError:
        pass
else:
    ModuleNotFoundError = ImportError
    FileNotFoundError = IOError
    FileExistsError = OSError
    from pytz import timezone
    from pytz import utc as timezone_utc
    try:
        import Tkinter as tk  # type: ignore
        # import ttk
        import tkMessageBox as messagebox  # type: ignore
    except ModuleNotFoundError:
        pass

from datetime import (  # noqa: F811
    datetime,  # import this *after* "from datetime" imports!
)


if __name__ == "__main__":
    from find_hierosoft import hierosoft  # noqa: F401
else:
    from blnk.find_hierosoft import hierosoft  # noqa: F401

from hierosoft import (  # noqa: F401
    echo0,
    echo1,
    echo2,
    set_verbosity,
    which,
)

from hierosoft import (
    replace_isolated,
    replace_vars,
    sysdirs,
)

from hierosoft.morelogging import (
    # set_syntax_error_fmt,
    # to_syntax_error,
    echo_SyntaxWarning,
    raise_SyntaxError,
    get_traceback,
    # view_traceback,
)

from hierosoft.logging2 import getLogger

logger = getLogger(__name__)

# Below is copied from a hierosoft comment
#   (shlex_join appears to not be in six, though shlex_quote is.
#   See feature request https://github.com/benjaminp/six/issues/386)
if sys.version_info.major > 3 and sys.version_info.minor >= 8:
    shlex_join = shlex.join
    shlex_quote = shlex.quote
else:
    import pipes
    shlex_quote = pipes.quote  # Slated for removal in Python 3.13

    def shlex_join(parts):
        result = ""
        sep = ""
        for part in parts:
            result += sep
            sep = " "
            if (" " in part) or ('"' in part):
                result += '"%s"' % part.replace('"', '\\"')
            else:
                result += part
        return result
    shlex.join = shlex_join


# Handle issues where the OS considers "BLNK" and all of these file
#   extensions as "text/plain" rather than allowing them to be
#   associated with separate programs.
associations = {
    ".kdb": ["keepassxc"],
    ".kdbx": ["keepassxc"],
    ".pyw": ["python"],
    ".py": ["python"],
    ".nja": ["ninja-ide", "-p"],  # required for opening project files
    ".csv": ["libreoffice", "--calc"],
    ".pdf": ["xdg-open"],  # changed below (See preferred_pdf_viewers loop)
}
if platform.system() == "Windows":
    if which("py") is not None:
        associations['.py'] = ["py", "-3"]
        associations['.pyw'] = ["py", "-3"]
else:
    if which("libreoffice") is None:
        if which("flatpak") is not None:
            associations[".csv"] = ["flatpak", "run", "--branch=stable",
                                    "--arch=x86_64", "--command=libreoffice",
                                    "org.libreoffice.LibreOffice", "--calc"]

# ^ Each value can be a string or list.
# ^ Besides associations there is also a special case necessary for
#   ninja-ide to change the file to the containing folder (See
#   associations code further down).
settings = {
    "file_type_associations": associations,
}

# preferred_pdf_viewers = ["qpdfview", "atril", "evince"]
# ^ evince is the GNOME and MATE "Document Viewer".
preferred_pdf_viewers = []

path = None
for try_pdf_viewer in preferred_pdf_viewers:
    path = which(try_pdf_viewer)
    if path is not None:
        associations[".pdf"][0] = try_pdf_viewer
        break
del path

'''
### XDG specification issue
There is apparently an issue in the XDG desktop spec where
Type=Desktop has no specified key for the path. Poikilos e-mailed
the XDG mailing list about it to report the issue (2022-11-02 from gmail
and it came back through the system indicating it was sent to list
members). I mentioned that blnk implements the suggested additions to
the specification.

Later I posted:
- <https://gitlab.freedesktop.org/xdg/xdg-utils/-/issues/210>

See also: "[Why not use Desktop
Entry](doc/development.md#Why not use Desktop Entry)" in
doc/development.md
'''


__doc__ = '''
Blnk
----
(pronounced "blink")
Make or run a shortcut to a file, directory, or URL,
storing the access time and other helpful information
about the target.

The blnk format is (based on the XDG .desktop file format):
{Template}

Cross-platform environment variables can be used, such as
`%USERPROFILE%`, `$HOME`, or `~`.


If you run such a file and blnk runs it in a text editor, the problem
is that the first line must be the Content-Type line shown (It is case
sensitive), and there must not be any blank line before it.

The following examples assume you've already made a symlink to blnk.py
as ~/.local/bin/blnk (and that ~/.local/bin is in your path--otherwise,
make the symlink as /usr/local/bin/blnk instead. On windows, make a
batch file that runs blnk and sends the parameters to it).

Create a shortcut:
blnk -s <target> [<name or path of new shortcut>]

Examples:
# Run a shortcut:
blnk <blnk file>
# Where <blnk file> is a path to a blnk file.
'''.format(Template=EXAMPLE_DATA)
# ^ OPTIONS: moved to parser (now parser.print_usage() is called by usage)

# - Type is "Directory" or "File"
# - Name may be shown in the OS but usually isn't (from XDG .desktop
#   format).
# - Exec is the path to actually run (a directory or file). Environment
#   variables are allowed (with the symbols shown):
#   - %USERPROFILES%


class FileTypeError(Exception):
    pass


def push_list(d, key, value):
    if key not in d:
        d[key] = []
    d[key].append(value)


def clean_shlex_join(parts):
    """Replace beginning of command with actual command.

    For example, sys.argv may start with
    ["/home/user/git/blnk/blnk/__init__.py", "--non-interactive"].
    """
    parts = list(parts)
    if parts[0].endswith("__init__.py"):
        parts[0] = "blnk"
    if parts[1] == "--non-interactive":
        del parts[1]
    return shlex.join(parts)


def not_quoted(s, key=""):
    '''
    Args:
        key (str): The name of the variable (only used
            for tracing).
    '''
    # a.k.a. no_enclosures
    key_msg = ""
    if key:
        key_msg = "{}=".format(key)
    if s is None:
        return None
    for q in ['"', "'"]:
        if (len(s) > 1) and s.startswith(q) and s.endswith(q):
            echo0("trimmed quotes from: {}{}".format(key_msg, s))
            return s[1:-1].replace("\\"+q, q)
            break
        else:
            echo0("using already not quoted {}: {}".format(key_msg, s))
    return s


def is_url(path):
    path = path.lower()
    endProtoI = path.find("://")
    if endProtoI > 0:
        # TODO: Check for known protocols? Check for "file" protocol?
        return True
    return False


def showMsgBoxOrErr(msg,
                    title="Blnk (Python {})".format(sys.version_info.major),
                    enable_gui=True):
    # from tkinter import messagebox
    echo0("{}\nusing {}".format(msg, title))
    logger.warning("enable_gui={}".format(enable_gui))
    if not enable_gui:
        return
    try:
        messagebox.showerror(title, msg)
    except tk.TclError as ex:
        if "no display" in str(ex):
            # "no display and no $DISPLAY environment variable"
            # (The user is not in a GUI session)
            pass
        else:
            raise ex


myBinPath = __file__
tryBinPath = os.path.join(sysdirs['LOCAL_BIN'], "blnk")
if os.path.isfile(tryBinPath):
    myBinPath = tryBinPath


class BLink:
    '''Blink Link
    Attributes:
        BASES (list[str]): A list of paths that could contain the
            directory if the directory is a drive letter that is not C
            but the os is not Windows.
        LINE_ACTIONS (list[str]): Types of lines. "Comments" is *not* a
            line type, because comments are added to
            self._comments[action]
        _comments (dict): _comments["Values"] and _comments["Sections"]
            are dicts(list[str]), but _comments["ContentType"]
            _comments["Top"] are list(str) (since there is only one
            ContentType and only comments could be before contenttype,
            though that may not work well). Each str should start with
            "#" unless it is a blank line.
    '''
    SECTION_GLOBAL = "\n"  # formerly NO_SECTION
    SECTION_BLINK = "X-Blnk"
    BASES = [
        sysdirs['HOME'],
    ]
    cloud_path = replace_vars("%CLOUD%")
    # ^ Does return None if the entire string is one var that is blank.
    cloud_name = None
    print('cloud_path="{}"'.format(cloud_path))
    if cloud_path is not None:
        # myCloud = myCloudName
        # if myCloud is None:
        #     myCloud = "Nextcloud"
        # os.path.join(sysdirs['HOME'], myCloud)
        BASES.insert(0, cloud_path)  # PREFER (place at [0]) since used for
        #   when drive letter not C: and OS is *not* Windows
        #   (may imply a Windows network drive, so other OS network
        #   drive first on another OS.)
        cloud_name = os.path.split(cloud_path)[1]
    print('cloud_name="{}"'.format(cloud_name))

    USERS_DIRS = ["Users", "Documents and Settings"]
    LINE_ACTIONS = ["ContentType", "Sections", "Values", "Top"]  # comment is N/A

    def __init__(self, path=None, assignmentOperator="=",
                 commentDelimiter="#", load=True,
                 blnk_format_only=True):
        self.contentType = None
        self.contentTypeParts = None
        self.lastSection = None
        self.path = None  # load sets this if succeeds
        self.assignmentOperator = assignmentOperator
        self.commentDelimiter = commentDelimiter
        self._comments = {}
        self.tree = OrderedDict()
        self.tree['X-Blnk'] = OrderedDict()
        self.tree['X-Target Metadata'] = OrderedDict()
        self.tree['X-Source Metadata'] = OrderedDict()

        for key in BLink.LINE_ACTIONS:
            if key.lower() in ("contenttype", "top"):
                # There is only one of each, so no dict
                self._comments[key] = []
            else:
                self._comments[key] = {}
                # ^ key is section or variable name, value is list(str)
        self._last_line_mode = None
        self._last_line_key = None
        if load:
            # raise_more (TypeError) since we are certain it *should be* a
            # blnk file by now (prevents running the file using the OS!)
            self.load(path, blnk_format_only=blnk_format_only)
        else:
            self.path = path

    def getAbs(self, path):
        rawPath = path
        if not os.path.exists(path):
            # See if it is relative to the blnk file.
            tryPath = os.path.join(os.path.dirname(self.path), path)
            if os.path.exists(tryPath):
                # path = os.path.realpath(tryPath)
                path = os.path.abspath(tryPath)
                print('* redirecting "{}" to "{}"'.format(rawPath, path))
        else:
            path = os.path.abspath(path)
        return path

    def splitLine(self, line, path=None, row=None):
        '''Parse a blnk formatted line.

        Args:
            line (str): One line in blnk file format. It cannot be a
                comment nor section heading.
            path (str, optional): The source of the data (only for
                tracing errors).
            row (str, optional): The source of the data in the file
                named path (only for tracing errors).
        '''
        i = line.find(self.assignmentOperator)
        if i < 0:
            tmpI = line.find(':')
            if tmpI >= 0:
                iPlus1C = line[tmpI+1:tmpI+2]
                iPlus2C = line[tmpI+2:tmpI+3]
                if (iPlus1C != "\\") or (iPlus2C == "\\"):
                    # ^ If iPlus2C == "\\", then the path may start with
                    # \\ (the start of a UNC network path).
                    self.assignmentOperator = ":"
                    echo0("* reverting to deprecated ':' operator for {}"
                          "".format(line))
                    i = tmpI
                else:
                    echo_SyntaxWarning(
                        path,
                        row,
                        "WARNING: The line contains no '=', but ':'"
                        " seems like a path since it is followed by"
                        " \\ not \\\\",
                    )
        if i < 0:
            raise_SyntaxError(path, row,
                              "The line contains no '{}': `{}`"
                              "".format(self.assignmentOperator, line))
        ls = line.strip()
        if self.isComment(ls):
            raise ValueError("splitLine doesn't work on comments.")
        if self.isSection(ls):
            raise ValueError("splitLine doesn't work on sections.")
        k = line[:i].strip()
        v = line[i+len(self.assignmentOperator):].strip()
        if self.commentDelimiter in v:
            # if k != "URL":
            echo_SyntaxWarning(
                path,
                row,
                "WARNING: `{}` contains a comment delimiter '{}'"
                " but inline comments are not supported."
                "".format(line, self.commentDelimiter),
            )
            # URL may have a # that is not a comment.
            # If the URL blnk file was automatically generated such as
            #   with the blnk -s command, then the Name and Comment will
            #   contain the character as well since they are generated
            #   from the target.
        return (k, v)

    def getSection(self, line):
        ls = line.strip()
        if ((len(ls) >= 2) and ls.startswith('[') and ls.endswith(']')):
            return ls[1:-1].strip()
        return None

    def isSection(self, line):
        return self.getSection(line) is not None

    def isComment(self, line):
        return line.strip().startswith(self.commentDelimiter)

    def _pushComment(self, comment):
        if comment.strip() and not self.isComment(comment):
            raise NotImplementedError(
                "Comment must be whitespace or start with comment mark")
        if self._last_line_mode == "Values":
            push_list(self._comments["Values"], self._last_line_key, comment)
        elif self._last_line_mode == "Sections":
            push_list(self._comments["Sections"], self._last_line_key, comment)
        elif self.contentType:
            self._comments["ContentType"].append(comment)
        else:
            self._comments["Top"].append(comment)

    def is_blnk(self):
        self.contentType == "text/blnk"

    def _pushLine(self, rawL, path=None, row=None, col=None):
        '''
        Args:
            rawL (str): a line in blnk format.
            path (str, optional): Show this path in syntax messages.
            row (int, optional): Show this row (such as line_index+1) in
                syntax messages.
            col (int, optional): Show this col (such as char_index+1) in
                syntax messages.
        '''
        line = rawL.strip()
        if len(line) < 1:
            return
        if row is None:
            if self.lastSection is not None:
                echo0("WARNING: The line `{}` was a custom line not on"
                      " a row of a file, but it will be placed in the"
                      " \"{}\" section which was still present."
                      "".format(line, self.lastSection))
        isContentTypeLine = False
        if line == "[X-Blnk]":
            isContentTypeLine = True
            value = "text/blnk"
            self.contentType = value
            self.contentTypeParts = [value]
        elif self.contentType is None:
            ctOpener = "Content-Type:"
            if line.startswith(ctOpener):
                isContentTypeLine = True
                values = line[len(ctOpener):].split(";")
                for i in range(len(values)):
                    values[i] = values[i].strip()
                value = values[0]
                self.contentType = value
                self.contentTypeParts = values
        if not self.is_blnk():
            logger.warning("* running non-blnk file directly")
            # NOTE: FileTypeError tells load to _choose_app
            raise FileTypeError(
                "The file must contain \"Content-Type:\""
                " (usually \"Content-Type: text/blnk\")"
                " before anything else, but"
                " _pushLine got \"{}\" (last file: {})"
                "".format(line, self.path)
            )
        if isContentTypeLine:
            self.lastSection = "X-Blnk"
            # Set _last_line_mode to prevent incompatible "Top" comment in save
            self._last_line_mode = "Sections"
            self._last_line_key = self.lastSection
            return
            # ^ For backward compatibility, don't actually require X-Blnk
            #   section (Return before that).

        trySection = self.getSection(line)
        # ^ OK since return occurred above if isContentTypeLine
        #   NOTE: SECTION is GLOBAL if so!
        if self.isComment(line):
            self._pushComment(line)
        elif trySection is not None:
            section = trySection
            if len(section) < 1:
                pre = ""  # This is a comment prefix for debugging.
                if row is not None:
                    if self.path is not None:
                        pre = self.path + ":"
                        if row is not None:
                            pre += str(row) + ":"
                            if col is not None:
                                pre += str(col) + ":"
                if len(pre) > 0:
                    pre += " "
                raise raise_SyntaxError(
                    path,
                    row,
                    pre+"_pushLine got an empty section",
                )
            else:
                self.lastSection = section
            self._last_line_mode = "Sections"
            self._last_line_key = self.lastSection
            logger.debug(
                "SECTION={}  # line={}"
                .format(
                    section.replace(BLink.SECTION_GLOBAL, "GLOBAL"), line))
        else:
            k, v = self.splitLine(line, path=path, row=row)
            '''
            if k == "Content-Type":
                self.contentType = v
                return
            '''
            self._last_line_mode = "Values"
            self._last_line_key = k
            section = self.lastSection
            if section is None:
                section = BLink.SECTION_GLOBAL
            sectionD = self.tree.get(section)
            if sectionD is None:
                if section != BLink.SECTION_GLOBAL:
                    raise NotImplementedError(
                        "Invalid section {} for {}={}"
                        .format(section, k, v))
                # else fall back to global section
                sectionD = OrderedDict()
                self.tree[section] = sectionD
            sectionD[k] = v
            logger.debug(
                "SET {}.{}={}".format(
                    section.replace(BLink.SECTION_GLOBAL, "GLOBAL"), k, v))

    def load(self, path, blnk_format_only=False):
        """Load a blnk file.
        *or* try to run a non-blnk file such as when the mimetype won't
        work and plain text files are associated with blnk (also useful
        for systems where other mimetypes are missing, so files can be
        associated with correct programs using blnk)

        Args:
            path (str): A blnk file (will try to run non-blnk if not
                blnk_format_only).
            blnk_format_only (bool, optional): Raise an exception if not
                in blnk format (Set to True if loading a blnk file for
                sure, otherwise set it to False). Defaults to False.

        Raises:
            FileNotFoundError: path doesn't point to an existing file
            UnicodeDecodeError: If ends with .blnk but is not Unicode.

        Returns:
            int: error code if running non-blnk fails
                file, otherwise 0.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError("\"{}\" does not exist.".format(path))
        try:
            with open(path, 'r') as ins:
                row = 0
                for line in ins:
                    row += 1
                    try:
                        self._pushLine(line, path=path, row=row)
                    except FileTypeError as ex:
                        # FIXME: See if FileTypeError is in python2
                        # Do not produce error messages for the bash
                        # script to show in the GUI since this is
                        # recoverable (and expected if plain text files
                        # are associated with blnk.
                        logger.error("{}: {}".format(type(ex).__name__, ex))
                        if blnk_format_only:
                            raise
                        logger.warning("* running file directly...")
                        return self._choose_app(path)
                self.lastSection = None
        except UnicodeDecodeError as ex:
            if path.lower().endswith(".blnk"):
                raise
            # else:
            # This is probably not a blnk file, so allow
            # the blank Exec handler to check the file extension.
            pass
        self.path = path
        return 0

    @property
    def options(self):
        return self.tree['X-Blnk']

    @property
    def meta(self):
        return self.tree['X-Target Metadata']

    @property
    def source(self):
        return self.tree['X-Source Metadata']

    @staticmethod
    def _get_target_type(options):
        return options.get("Type")

    @staticmethod
    def _get_target_key(options):
        target_type = BLink._get_target_type(options)
        if not target_type:
            return None
        return TARGET_MAP[target_type]

    @staticmethod
    def _get_target(options):
        valid_target_key = BLink._get_target_key(options)
        if not valid_target_key:
            return None
        return options.get(valid_target_key)

    @property
    def target_type(self):
        return self.tree["X-Blnk"].get("Type")

    @property
    def target_key(self):
        if not self.target_type:
            return None
        return TARGET_MAP[self.target_type]

    @property
    def target(self):
        valid_target_key = self.target_key
        if not valid_target_key:
            return None
        return self.tree["X-Blnk"].get(valid_target_key)

    def save(self, path, overwrite=False):
        # if not path:
        #     path = self.path
        results = {}
        if not self.target:
            raise RuntimeError(
                "Call set_target or analyze_target first"
                " (missing self.target).")
        if not self.target_key:
            raise RuntimeError(
                "Call set_target or analyze_target first"
                " (missing self.target_key).")
        if not self.target_type:
            raise RuntimeError(
                "Call set_target or analyze_target first"
                " (missing self.target_type).")
        missing = []
        for section_name, r_sections in REQUIREMENTS[self.target_type].items():
            d_sections = DEFAULTS[self.target_type][section_name]
            if section_name not in self.tree:
                missing.append("{} section".format(section_name))
                continue
            for key, value in d_sections.items():
                if value is None:
                    continue
                if self.tree[section_name].get(key) is None:
                    self.tree[section_name][key] = value
            for key, value in r_sections.items():
                if self.tree[section_name].get(key) is None:
                    missing.append("{} in {}".format(key, section_name))
        if missing:
            results["error"] = ("Missing fields required for {}"
                                .format(self.target_type))
            results["missing"] = missing
            logger.error(
                "Error: Missing {} required for {}"
                .format(results["missing"], self.target_type))
            return results

        self.path = path

        if os.path.exists(path):
            if not path.lower().endswith(".blnk"):
                raise FileExistsError(
                    "Refusing to overwrite non-blnk file \"{}\"!"
                    .format(path))
        if os.path.exists(path) and not overwrite:
            echo0("Error: {} already exists.".format(path))
            return 1

        with open(path, 'w') as outs:
            self._save(outs)
        logger.info("* wrote \"{}\"".format(path))

        return results

    def _write_comment(self, stream, comment):
        if "\r" in comment:
            raise ValueError("\\r not allowed in comment")
        if "\n" in comment:
            raise ValueError("\\n not allowed in comment")
        stream.write(comment+"\n")

    def _save(self, stream):
        if not self.target_type:
            raise RuntimeError(
                "Call set_target first (missing Type).")
        if not self.target_key:
            raise RuntimeError(
                "Call set_target first (missing valid Type).")
        if not self.target:
            raise RuntimeError(
                "Call set_target first (missing {})."
                .format(self.target_key))
        if self._comments["Top"]:
            self._write_comment(stream, "# Top")
            for line in self._comments["Top"]:
                self._write_comment(stream, line)
        if self._comments["ContentType"]:
            self._write_comment(stream, "# ContentType")
            # Deprecated, so carry over by writing first
            for line in self._comments["ContentType"]:
                self._write_comment(stream, line)
        commented = set()
        for section, meta in self.tree.items():
            stream.write("[{}]\n".format(section))
            c_key = "Sections"
            if self._comments[c_key].get(section):
                for line in self._comments[c_key][section]:
                    self._write_comment(stream, line)
            for key, value in meta.items():
                if self.assignmentOperator in key:
                    raise KeyError(
                        "'{}' is not allowed in a variable name"
                        .format(self.assignmentOperator))
                # if key == self.target_key:
                #     stream.write(
                #         ("{}{}"+Exec_fmt+"\n").format(
                #             key, self.assignmentOperator, value
                #         )
                #     )
                # else:
                stream.write(
                    "{}{}{}\n".format(key, self.assignmentOperator, value))
                c_key = "Values"
                # Write keys's comments
                if self._comments[c_key] and self._comments[c_key].get(key):
                    if key not in commented:
                        commented.add(key)
                        for line in self._comments[c_key][key]:
                            self._write_comment(stream, line)
                    else:
                        logger.warning(
                            "Warning: already saved comment for {key}"
                            " under first {key}.".format(key=key))

            stream.write("\n")
        for k, v in self._comments["Values"].items():
            if k not in commented:
                raise NotImplementedError(
                    "Discarded comment=\"{}\" for key={}"
                    .format(v, k))

    def validate_path(self, blnk_path, target, options, overwrite=False):
        results = {}
        if not blnk_path.lower().endswith(".blnk"):
            raise FileExistsError("Refusing to overwrite non-blnk \"{}\"!"
                                  .format(blnk_path))
        error = (
            "Error: {} already exists."
            " Use --update to run analyze_metadata instead."
            .format(blnk_path))

        if options['Type'] in ["Directory", "File"]:
            if not os.path.exists(target):
                error += (" However, this will not work with {}"
                          " since it does not exist."
                          .format(target))
        elif options['Type'] == "Exec":
            error += (" However, this will not work with {} since"
                      " it is not an existing plain executable file."
                      .format(target))
        elif options['Type'] == "URL":
            error += (" However, this will not work with {}"
                      " since it is not a File nor Directory."
                      .format(target))
        else:
            raise ValueError("Unknown type {}".format(options.get("Type")))
        if error:
            results["error"] = error
        return results

    def set_target(self, target, options, target_key='Exec',
                   enable_gui=True, overwrite=False):
        """Set the target of the shortcut.

        Arguments:
            options (dict): Values for the shortcut using keys that are the
                same names as used in XDG shortcut format. You must at least
                set: 'Terminal' (True will be changed to "true", False to
                "false"), 'Type' (Name will be generated from target's
                ending if None).
            enable_gui (bool, optional): Try to show a tk messagebox
                for errors if True.
            target_key (str, optional): Set to 'URL' if target is a URL.
                Defaults to "Exec".
        """
        results = {}
        if self.path and os.path.isfile(self.path):
            results = self.validate_path(self.path, target, options,
                                         overwrite=overwrite)
            error = results.get("error")
            # logger.error(error)
            results["error"] = error
            return results

        # else path is not known yet (See "Name" below).

        if target.lower().endswith(".blnk"):
            # FIXME: See if FileTypeError is in Python 2 or create polyfill
            raise FileTypeError(
                "Refusing to point blnk to another blnk \"{}\"!"
                .format(target))

        if options["Type"] not in TARGET_MAP:
            raise ValueError("Type should be among: {}"
                             .format(list(TARGET_MAP.keys())))
        valid_target_key = TARGET_MAP[options["Type"]]
        if target_key != valid_target_key:
            warning = (
                "Warning: changed target_key '{}' to {} for {}"
                .format(target_key, valid_target_key, options["Type"]))
            logger.warning(warning)
            target_key = valid_target_key
        if options.get('Name') is None:
            if target_key == "URL":
                # May be automatically set by cli. See uses of name_from_url.
                raise ValueError(
                    "You must provide a 'Name' option for this URL.")

            if target.endswith(os.path.sep):
                if target != "/":
                    target = target[:-len(os.path.sep)]
            # echo1('Using target: "{}"'.format(target))
            if os.path.isfile(target):
                options["Name"] = \
                    os.path.splitext(os.path.split(target)[-1])[0]
                # ^ Also should be done to calculate options['Name'] before
                #   calling this function if done automatically.
            elif os.path.isdir(target):
                # Do not remove ".*" from a folder name
                #   (otherwise ".dir" would become "" and
                #   "cron.daily" would become "cron")!
                options["Name"] = os.path.split(target)[-1]
        else:
            logger.warning(
                "Using specified name=\"{}\"".format(options['Name']))

        newName = options["Name"] + ".blnk"
        newPath = newName
        _, name = os.path.split(newPath)
        if name.startswith("."):
            logger.warning(
                "Warning: creating hidden file {}".format(newPath))

        if os.path.isfile(newPath):
            results = self.validate_path(newPath, target, options,
                                         overwrite=overwrite)
            error = results.get("error")
            # logger.error(error)
            results["error"] = error
            return results

        if options.get('Type') is None:
            raise KeyError("Type is required.")
        if options.get('Terminal') is None:
            raise KeyError(
                'Terminal (with value True, False,'
                ' "true" or "false" is required'
            )
        if options['Terminal'] is True:
            options['Terminal'] = "true"
        elif options['Terminal'] is False:
            options['Terminal'] = "false"
        # ^ Use the current directory, so do not use the full path.
        # INFO: The included shortcut will redirect stderr (then show
        # the log at the end if not empty).

        if os.path.isfile(target) or os.path.isdir(target):
            self.analyze_target(options, target_key=target_key,
                                enable_gui=enable_gui, target=target)
        else:
            raise FileNotFoundError(
                "load_target can only work with existing files.")
        self.path = newPath
        if not self.path:
            raise NotImplementedError("self.path was not generated")
        return results

    def analyze_target(self, options, target_key="Exec",
                       enable_gui=True, target=None):
        results = {}
        if options is None:
            options = self.options
        if target is None:
            # It is *not* new, so target property's leaf should be set
            #   by load.
            target = self.target
        if not target:
            raise RuntimeError(
                "Set target (usually via load or set_target"
                " which are mutually exclusive)"
                " before analyze_target")
        mtime = None
        ctime = None
        echo1('Using target: "{}"'.format(target))
        mtime_ts = pathlib.Path(target).stat().st_mtime
        mtime = datetime.fromtimestamp(mtime_ts, tz=timezone_utc)
        ctime_ts = pathlib.Path(target).stat().st_ctime
        ctime = datetime.fromtimestamp(ctime_ts, tz=timezone_utc)
        # ^ stat raises FileNotFoundError if not os.path.exists
        # TODO: test both on mac, and if necessary use
        #   os.stat(target).st_birthtime "To get file creation time on Mac
        #   and some Unix based systems."
        #   -<https://pynative.com/python-file-creation-modification-datetime/>
        '''
        As per <https://blog.ganssle.io/articles/2019/11/utcnow.html
        :~:text=timestamp()%20method%20gives%20a,
        time%2C%20even%20if%20you%20originally>:
        tz=timezone_utc correctly (in Python 3 only?) makes the
        output utilize timezone. For example:
        str(mtime) output (during DST):
        2022-08-09 14:39:55.144246
        changes to:
        2022-08-09 18:39:55.144246+00:00
        (Note that the output of the GNU stat command uses a different
        notation:
        Modify: 2022-08-09 14:39:55.144246010 -0400
        )
        '''
        # hostname = platform.node()
        hostname = socket.gethostname()
        # socket.gethostname() may be FQDN on Fedora (according to a comment
        #   on <https://stackoverflow.com/a/4271755/4541104>).
        for key, value in options.items():
            # Must set self.tree["X-Blnk"]["Type"]
            self.tree["X-Blnk"][key] = value

        Exec_fmt = "{}"
        if os.path.exists(target) and (" " in target):
            Exec_fmt = '"{}"'

        self.tree["X-Blnk"]["Comment"] = \
            "Created using '{}'".format(clean_shlex_join(sys.argv))

        if options['Type'] in ["Directory", "File", "Exec"]:
            self.tree["X-Target Metadata"]["modified"] = mtime
            self.tree["X-Target Metadata"]["created"] = ctime

        self.tree["X-Source Metadata"]["hostname"] = hostname
        valid_target_key = TARGET_MAP[options["Type"]]
        if options['Type'] in ["Directory", "File"]:
            # target key will be changed automatically
            pass
        elif target_key != valid_target_key:
            error = (
                "Error: target_key {} should be {} for Type {}"
                .format(target_key, valid_target_key, options["Type"]))
            raise ValueError(error)

        if options['Type'] in ["Directory", "File"]:
            # In XDG desktop format:
            # - The file extension would be ".directory" for a directory
            # - There is no "File" type (Only Application, Link, and
            #   Directory are valid).
            # - The desktop-file-validate command can diagnose issues.
            # - See also "XDG specification issue" comment further up.
            # NOTE: options['Type'] is above,
            #   but target_key could be Exec, so fix it:
            if target_key != valid_target_key:
                warning = (
                    "Warning: target_key {} changed to {} for Type {}"
                    .format(target_key, valid_target_key, options["Type"]))
                logger.warning(warning)
                target_key = valid_target_key
            self.tree["X-Blnk"][target_key] = Exec_fmt.format(target)

            # target_key = options["Type"]
        elif target_key == 'Exec':
            self.tree["X-Blnk"][target_key] = Exec_fmt.format(target)
            # "Terminal" already set in this case (iterated options above)
        elif target_key == "URL":
            if options['Type'] != "Link":
                raise RuntimeError(
                    "The type for target URL should be Link but is {}"
                    "".format(options['Type'])
                )
            self.tree["X-Blnk"][target_key] = Exec_fmt.format(target)
            accessed = datetime.now(tz=timezone_utc)
            self.tree["X-Target Metadata"]["accessed"] = accessed
            # "Name", "Type" already set in this case (iterated options above)
            # Technically, "Terminal" could be useful for non-browser data
            #   such as json URLs.
        else:
            raise NotImplementedError("target_key={}".format(target_key))
        # echo0(content)
        if not self.target_type:
            raise NotImplementedError("Setting target Type failed.")
        if not self.target_key:
            raise NotImplementedError("Setting target_key failed.")
        return results

    def getBranch(self, section, key):
        '''Get the actual section and the value.

        Returns:
            tuple(str): section (section name key for self.tree) and
                value self.tree[section][key]. The reason section is
                returned is in case the key doesn't exist there but
                exists in another section.
        '''
        v = None
        sectionD = self.tree.get(section)
        if sectionD is not None:
            v = sectionD.get(key)
        if v is None:
            section = None
            for trySection, sectionD in self.tree.items():
                v = sectionD.get(key)
                if v is not None:
                    section = trySection
                    break
        return section, v

    def get(self, key):
        section = BLink.SECTION_GLOBAL
        got_section, v = self.getBranch(section, key)
        if got_section is None:
            # It is using the latest format.
            got_section, v = self.getBranch("[X-Blnk]", key)
        # old_v = v
        v = not_quoted(v, key=key)
        return v

    def getExec(self, key='Exec', split=None):
        '''Get Exec (or another key) from the blnk file.

        Be careful when filling in paths from cwd here. This function
        will keep the quotes to ensure paths with spaces work, and to
        ensure the original syntax of the line is kept.

        Args:
            key (str, optional): Key desired. Defaults to "Exec".
            split (bool, optional): Whether to use shlex.split
                to analyze it (for cross-platform corrections).
                Defaults to False *unless* key is 'Path' then True.

        Returns:
            tuple(str): value of Exec or other specified key, then error
                or None.
                - *Always* use shlex.split on the return (if not None),
                  even if Type is not "Application", because single
                  quotes need to be removed!
        '''
        prefix = "[getExec] "  # noqa: F841
        if split is None:
            split = (key == 'Exec')
        trySection = BLink.SECTION_BLINK  # formerly BLink.SECTION_GLOBAL
        section, v = self.getBranch(trySection, key)
        # Warning: don't remove quotes yet, because shlex.split
        #   is done later! Removing the quotes now would split more
        #   parts than should be.
        # logger.debug(prefix+"got v={}".format(v))

        if v is None:
            path = self.path
            if path is not None:
                path = "\"" + path + "\""
            msg = ("WARNING: There was no \"{}\" variable in {}"
                   "".format(key, path))
            return None, msg
        elif section != trySection:
            sectionMsg = section
            if section == BLink.SECTION_GLOBAL:
                sectionMsg = "the main section"
            else:
                sectionMsg = "[{}]".format(section)
            msg = "WARNING: \"{}\" was in {}".format(key, sectionMsg)
        if v is None:
            return None, msg
        path = v

        if path.startswith("~/"):
            if platform.system() == "Windows":
                if split:
                    shlex.split(path)
                    # Only replace "/" in command
                    #   (other args may be switches) if
                    #   Type is "Application"
                    path[0] = path[0].replace("/", "\\")
                else:
                    path = path.replace("/", "\\")
            path = os.path.join(sysdirs['HOME'], path[2:])

        if platform.system() == "Windows":
            if v[1:2] == ":":
                if (len(v) > 2) and (v[2:3] != "\\"):
                    raise ValueError(
                        "The third character should be '\\' when the"
                        " 2nd character is ':', but the Exec value was"
                        " \"{}\"".format(v)
                    )
                # elif == 2 allow drive letter shortcut without slash

        else:  # Not windows

            # Rewrite Windows paths **when on a non-Windows platform**:
            # logger.debug("  [blnk] v: \"{}\"".format(v))

            if v[1:2] == ":":
                # ^ Unless the leading slash is removed, join will
                #   ignore the param before it (will treat it as
                #   starting at the root directory)!
                # logger.debug("  v[1:2]: '{}'".format(v[1:2]))
                if v.lower() == "c:\\tmp":
                    path = sysdirs['TMP']
                    echo1(prefix+"  [blnk] Detected {} as {}"
                          "".format(v, sysdirs['TMP']))
                elif v.lower().startswith("c"):
                    echo1(prefix+"  [blnk] Detected c: in {}"
                          "".format(v.lower()))
                    path = v[3:].replace("\\", "/")
                    rest = path
                    # ^ Cut off C:\, so path may start with Users now:
                    statedUsersDir = None
                    for thisUsersDir in BLink.USERS_DIRS:
                        tryPath = thisUsersDir.lower() + "/"
                        if path.lower().startswith(tryPath):
                            statedUsersDir = thisUsersDir
                            break
                        else:
                            echo1("  [blnk] {} doesn't start with {}"
                                  "".format(path.lower(),
                                            thisUsersDir.lower() + "/"))
                    echo1("  [blnk] statedUsersDir: {}"
                          "".format(statedUsersDir))
                    if statedUsersDir is not None:
                        parts = path.split("/")
                        # logger.debug("  [blnk] parts={}".format(parts))
                        if len(parts) > 1:
                            rel = ""
                            if len(parts[2:]) > 0:
                                rel = parts[2:][0]
                                old = parts[:2][0]
                                if len(parts[2:]) > 1:
                                    rel = os.path.join(*parts[2:])
                                if len(parts[:2]) > 1:
                                    old = os.path.join(*parts[:2])
                                # ^ splat ('*') since join takes
                                #   multiple params not a list.
                                echo1("  [blnk] changing \"{}\" to"
                                      " \"{}\"".format(old, sysdirs['HOME']))
                                path = os.path.join(sysdirs['HOME'], rel)
                            else:
                                path = sysdirs['HOME']
                        else:
                            path = sysdirs['HOME']
                    elif path.lower() == "users":
                        path = sysdirs['PROFILESFOLDER']
                    else:
                        path = os.path.join(sysdirs['HOME'], rest)
                        echo0("  [blnk] {} was forced due to bad path:"
                              " \"{}\".".format(path, v))
                else:
                    echo0("Detected drive letter that is not C:")
                    # It starts with letter+colon but letter is NOT c.
                    path = v.replace("\\", "/")
                    rest = path[3:]
                    isGood = False
                    for thisBase in BLink.BASES:
                        echo1("  [blnk] thisBase: \"{}\""
                              "".format(thisBase))
                        echo1("  [blnk] rest: \"{}\""
                              "".format(rest))
                        tryPath = os.path.join(thisBase, rest)
                        echo1("  [blnk] tryPath: \"{}\""
                              "".format(tryPath))
                        if os.path.exists(tryPath):
                            path = tryPath
                            # Change something like D:\Meshes to
                            # /home/x/Nextcloud/Meshes or use some other
                            # replacement for D:\ that is in BASES.
                            logger.warning(
                                "  [blnk] {} was detected."
                                .format(tryPath))
                            isGood = True
                            break
                        else:
                            echo0("  [blnk] {} doesn't exist."
                                  "".format(tryPath))
                    if not isGood:
                        # Force it to be a non-Window path even if it
                        # doesn't exist, but use the home directory
                        # so it is a path that makes some sort of sense
                        # to everyone even if they don't have the
                        path = os.path.join(sysdirs['HOME'], rest)
                        echo0("  [blnk] {} was forced due to bad path:"
                              " \"{}\".".format(path, v))
            else:
                path = v.replace("\\", "/")

        path = replace_vars(path)

        if BLink.cloud_name is not None:
            for statedCloud in ["ownCloud", "owncloud"]:
                path = replace_isolated(path, statedCloud,
                                        BLink.cloud_name,
                                        case_sensitive=False)

        # logger.debug(prefix+"got path={}".format(path))
        if platform.system() == "Windows":
            # old_parts = shlex.split(path)
            # ^ removes backslashes \ !!
            #   https://github.com/mesonbuild/meson/issues/5726
            old_parts = shlex.split(shlex_quote(path))
            for i in range(len(old_parts)):
                old_parts[i] = old_parts[i].replace("\\\\", "\\")
                if ((len(old_parts[i]) >= 2) and old_parts[i].startswith("'")
                        and old_parts[i].endswith("'")):
                    # Remove escaped and enclosing single quotes
                    old_parts[i] = old_parts[i][1:-1]
                    old_parts[i] = old_parts[i].replace("\\'", "'")
                    # ^ replace it *2nd* since may end in
                    #   literal `\` then bad `'` until bad `'`s are
                    #   removed.
        else:
            old_parts = shlex.split(path)

        # logger.debug(prefix+"got old_parts={}".format(old_parts))

        # if not os.path.exists(old_parts[0]):
        abs0 = self.getAbs(old_parts[0])
        if old_parts[0] == abs0:
            if not os.path.exists(old_parts[0]):
                logger.warning(
                    "  [blnk] \"{}\""
                    " wasn't an existing absolute or relative path"
                    .format(old_parts[0]))
        old_parts[0] = abs0

        # NOTE: Extra '' marks should *not* matter, since no_quotes is used
        # if len(old_parts) == 1:
        #     # Prevent adding extra '' marks
        #     path = old_parts[0]
        # else:
        if split:
            path = shlex.join(old_parts)

        # else:
        #    print('* using existing relative target "{}"'.format(old_parts))

        if path != v:
            logger.warning(prefix+"changed \"{}\" to \"{}\"".format(v, path))
        return path, None

    @staticmethod
    def _run_parts(parts, check=True, cwd=None, target_blnk_type=False):
        '''Run a command (list of command and args) directly
        using the best call depending on the Python version.

        Args:
            cwd (str, optional): Change to this working directory first.
                This should not usually be set to anything except the
                Path field of a .blnk (or .desktop) file.
                - Warning: A value other than None will cause subprocess
                  to FileNotFoundError for some reason if running
                  `['xdg-open', DirectoryPath]`.
            target_blnk_type (bool, optional): You can set this to True
                if the file type is associated with blnk to prevent
                infinite recursion between xdg-open and blnk.
            check (bool, optional): Set the "check" option of subprocess
                if available in the version of Python that is running
                this module.
        '''
        if cwd is not None:
            if not_quoted(cwd) != cwd:
                raise ValueError("cwd must not be quoted!")
        for i in range(len(parts)):
            if not_quoted(parts[i]) != parts[i]:
                raise ValueError(
                    "parts[{}] must not be quoted but is {}!"
                    "".format(i, parts[i])
                )
        if (len(parts) > 1) and (parts[1] == cwd):
            echo0('Warning: not using cwd="{}" since that is the target.'
                  ''.format(cwd))
            cwd = None
        # if cwd is not None:
        #     os.chdir(cwd)
        # ^ Use the cwd param of run or check_call instead.
        logger.warning(
            '* running "{}" (in "{}")...'.format(parts, os.getcwd()))
        if target_blnk_type and (parts[0] == "xdg-open"):
            raise ValueError(
                'xdg-open was blocked to prevent infinite recursion'
                ' in case the file type of {} is associated with blnk.'
                ''.format(parts[1:])
            )
        # else: There should be no infinite recursion if the document is
        #   not a type associated with blnk such as plain text.

        run_fn = subprocess.check_call
        run_fn_name = "subprocess.check_call"
        use_check = False
        if len(parts) > 1:
            if not os.path.exists(parts[1]):
                logger.warning('"{}" does not exist.'.format(parts[1]))
            else:
                logger.info('"{}" was found.'.format(parts[1]))
        if hasattr(subprocess, 'run'):
            # Python 3
            use_check = True
            run_fn = subprocess.run
            run_fn_name = "subprocess.run"
            logger.warning("  - run_fn=subprocess.run")
            part0 = which(parts[0])
            # if localPath not in os.environ["PATH"].split(os.pathsep):
            if part0 is None:
                part0 = which(parts[0], more_paths=[sysdirs['LOCAL_BIN']])
                if part0 is not None:
                    parts[0] = part0
        else:
            logger.warning(
                "  - using Python 2 subprocess.check_call"
                " from Python {}"
                .format(sys.version_info.major))
            # check_call requires a full path (!):
            if not os.path.isfile(parts[0]):
                part0 = which(parts[0], more_paths=[sysdirs['LOCAL_BIN']])
                if part0 is not None:
                    parts[0] = part0
        completedprocess = None
        returncode = None
        try:
            echo1("run_fn={}".format(run_fn_name))
            if use_check:
                echo1("* using check")
                if cwd is not None:
                    echo1("* manually-set cwd is None")
                    # parts[0] = which(parts[0])
                    echo1('parts[0]="{}"'.format(parts[0]))
                    # Warning: If cwd is not None subprocess will raise
                    #   FileNotFoundError if running
                    #   ['xdg-open', DirectoryPath]!
                    completedprocess = run_fn(parts, check=check, cwd=cwd)
                else:
                    echo1("* manually-set cwd is {}".format(cwd))
                    completedprocess = run_fn(parts, check=check)
            else:
                echo1("* not using check")
                if cwd is not None:
                    echo1("* manually-set cwd is None")
                    completedprocess = run_fn(parts, cwd=cwd)
                else:
                    echo1("* manually-set cwd is {}".format(cwd))
                    completedprocess = run_fn(parts)
            if completedprocess is not None:
                if hasattr(completedprocess, "returncode"):
                    returncode = completedprocess.returncode
            echo0("returncode={}".format(completedprocess.returncode))
        except FileNotFoundError as ex:
            echo0("parts={}".format(parts))
            pathMsg = (" (The system path wasn't checked"
                       " since the executable part is a path)")
            if os.path.split(parts[0])[1] == parts[0]:
                # It is a filename not a path.
                pathMsg = (" ({} may not be in the system path,"
                           " or maybe blnk set cwd and shouldn't have)"
                           "".format(parts[0]))
            raise FileNotFoundError(
                "Running external application `{}` for a non-blnk file"
                " failed{}:"
                " {}".format(shlex.join(parts), pathMsg, ex),
            )
        except FileNotFoundError as ex:
            echo0(get_traceback())
            raise FileNotFoundError(
                'The file was not found: '
                ' {} ({})'.format(shlex.join(parts), ex),
            )
        except Exception as ex:
            raise ex
        '''
        except TypeError as ex:
            # should only happen if sending check=check when run_fn
            # is check_call--which doesn't work since check is only a
            # keyword argument when run_fn is run.
            if "unexpected keyword argument 'check'" in str(ex):
                try:
                    run_fn(parts)
                except FileNotFoundError as ex:
                    raise ex
            else:
                raise ex
        '''
        if returncode is None:
            returncode = 1
        # else should have been set to completedprocess.returncode
        return returncode

    @staticmethod
    def _run(Exec, Type, cwd=None):
        '''Run the correct path using the Type variable from the blnk
        This is a static method, so any object attributes must be
        provided as arguments.

        Note that the "Path" key sets the working directory NOT the
        target, but the Exec argument is equivalent to 'Exec'.

        Args:
            Exec (str): Should be the Exec value if Type is Application,
                Path if a File or Directory, or URL if a Link.
            Type (str): "Directory", "File", OR "Application"
            cwd (str, optional) Set this to the value of the 'Path' key
                if present to set the current working directory in the
                subprocess.
        '''
        echo1('* _run("{}", "{}", cwd="{}")'.format(Exec, Type, cwd))
        # tryCmd = "geany"  # See `app` variable instead.
        # TODO: try os.popen('open "{}"') on mac
        # NOTE: %USERPROFILE%, $HOME, ~, or such should already be
        #   replaced by getExec.
        exists_fn = os.path.isfile
        execParts = shlex.split(Exec)
        if len(execParts) > 1:
            Exec = execParts[0]
        if Type == "Directory":
            exists_fn = os.path.isdir
        elif Type == "Application":
            echo0('* running application {}'.format(execParts))
            return BLink._run_parts(execParts, check=True, cwd=cwd)
        elif Type == "Link":
            def true_fn():
                echo0('* assuming "{}" exists.'.format(Exec))
                return True
            exists_fn = true_fn

        if platform.system() == "Windows":
            if (len(Exec) >= 2) and (Exec[1] == ":"):
                # starts with "C:" or another drive letter
                if not os.path.exists(Exec):
                    raise FileNotFoundError(
                        "The Exec target doesn't exist: {}"
                        "".format(Exec)
                    )
            os.startfile(Exec, 'open')
            # run_fn('cmd /c start "{}"'.format(Exec))
            return 0
        if Type == "Directory":
            echo0('* opening directory "{}"'.format(Exec))
            execParts = ['xdg-open', not_quoted(Exec, key='_run() arg')]
            return BLink._run_parts(execParts, check=True, cwd=cwd)
        thisOpenCmd = None
        if "://" not in Exec:
            if not exists_fn(Exec):
                raise FileNotFoundError(
                    '"{}"'
                    ''.format(Exec)
                )
        if Type == "Link":
            thisOpenCmd = 'xdg-open'
            '''
            if len(parts) == 1:
                raise ValueError(
                    "_run expected ['xdg-open', '{}'] (or some program"
                    " for opening a URL) but only got {}"
                    "".format(parts[1], parts)
                )
            '''
            return BLink._run_parts([thisOpenCmd, Exec], check=True)
        try:
            if Type == "File":
                # thisOpenCmd = tryCmd
                # FIXME: There should be a better way to solve this. The
                #   infinite recursion only happens if the type of file
                #   being opened (The file type of the path in the Exec
                #   line) is associated with blnk.
                echo0("  - thisOpenCmd={}...".format(thisOpenCmd))
                if thisOpenCmd == "xdg-open":
                    raise ValueError(
                        '{} was blocked to prevent infinite'
                        ' recursion in case the file type of {} is'
                        ' associated with blnk.'
                        ''.format(thisOpenCmd, Exec)
                    )
                return BLink._run_parts([thisOpenCmd, Exec], check=True)
        except OSError as ex:
            try:
                echo0(str(ex))
                thisOpenCmd = "open"
                logger.warning("  - thisOpenCmd={}...".format(thisOpenCmd))
                return BLink._run_parts([thisOpenCmd, Exec], check=True)
            except OSError as ex2:
                echo0(str(ex2))
                thisOpenCmd = "xdg-launch"
                logger.warning("  - trying {}...".format(thisOpenCmd))
                return BLink._run_parts([thisOpenCmd, Exec], check=True)
        except subprocess.CalledProcessError as ex:
            # raise subprocess.CalledProcessError(
            #     "{} couldn't open the Exec target: \"{}\""
            #     "".format(thisOpenCmd, Exec)
            # )
            raise ex
        return 1  # This should never happen.

    def _choose_app(self, path):
        '''Choose an application and run it.
        if either it isn't a blnk file at all or
        Type is "File" (only use _run instead of _choose_app if Type is
        Application).
        '''
        global settings
        prefix = "_choose_app"
        cwd = None
        # cwd = os.path.dirname(os.path.realpath(self.path))
        # logger.info('  - set cwd="{}"'.format(cwd))
        # ^ Leave cwd as None since it should only be set by
        #   the 'Path' key of the shortcut.
        logger.warning("  - choosing app for \"{}\"".format(path))
        app = "geany"
        # If you set blnk to handle unknown files:
        more_parts = []
        orig_app = app
        cmd_parts = None
        more_missing = []
        associations = settings['file_type_associations']
        for dotExt, args in associations.items():
            if path.lower().endswith(dotExt):
                if isinstance(args, list):
                    app = args[0]
                    more_parts = args[1:]
                else:
                    app = args
                if which(app) is not None:
                    break
                else:
                    more_missing.append(app)
                # else keep looking for other options
                if which(app) is not None:
                    app = which(app)  # in case not in path
                cmd_parts = [app] + more_parts + [path]

        # shlex.split is NOT necessary since _choose_app should
        # NOT run for executables (Type=Application).

        '''
        absPath = self.getAbs(path)
        if os.path.splitext(path)[1] == "" and os.access(absPath, os.X_OK):
            # app = path
            # more_parts = []
            cmd_parts =
        '''
        if which(app) is None:
            echo0(prefix+"{} is not in the system PATH.".format(app))
            dotExt = os.path.splitext(path)[1]
            missing_msg = ""
            if len(more_missing) > 0:
                missing_msg = " (and any of: {})".format(more_missing)
            logger.warning(
                '    "{}"{} is missing so {} will open {}.'
                .format(app, missing_msg, orig_app, dotExt))
            app = orig_app
            more_parts = []
        else:
            app = which(app)
        if path.lower().endswith(".nja"):
            path = os.path.split(path)[0]
            # ^ With the -p option, Ninja-IDE will only open a directory
            #   (with or without an nja, but not the nja file directly).
        logger.warning("    - app={}".format(app))
        if cmd_parts is None:
            return BLink._run_parts(
                [app] + more_parts + [path],
                cwd=cwd,
            )
        else:
            return BLink._run_parts(
                cmd_parts,
                cwd=cwd,
            )

    def run(self):
        '''Run the BLink object.
        '''

        '''
        section = None
        section, Type = self.getBranch(BLink.NO_SECTION, 'Type')
        if Type is None:
            section = "[X-Blnk]"
            section, Type = self.getBranch(section, 'Type')
        echo1("[{}] Type={}".format(section, Type))
        '''
        Type = self.get('Type')  # ^ replaces all of the above
        echo1("Type={}".format(Type))

        if Type == "Link":
            url = self.get('URL')
            if url is None:
                raise SyntaxError(
                    "if Type={} then URL should be set.".format(Type)
                )
            return BLink._run(url, Type)
        source_key = 'Exec'
        split = True
        if self.get('Type') in ["Directory", "File"]:
            # old_v = self.get('Exec')
            try_v = self.get('Path')
            if try_v is not None:
                # Created by a version of blnk >= 2022-11-02
                # 1:00 PM ET
                source_key = 'Path'
                # ^ blnk uses Path at least until
                #   gitlab.freedesktop.org/xdg/xdg-utils/-/issues/210
                #   is resolved.
                split = False

        execStr, err = self.getExec(key=source_key, split=split)
        # ^ Adds single quotes as necessary!
        # ^ Makes the path absolute
        if self.get('Type') in ["Directory", "File"]:
            if not execStr:
                raise KeyError("Missing {}".format(source_key))
            if not os.path.exists(not_quoted(execStr)):
                raise FileNotFoundError('There is no "{}"'
                                        .format(execStr))
            # Do *not change to not_quoted yet* though, or _run
            #   will split it wrong if there are spaces!
        # exec_parts = None
        if err is not None:
            echo0(err)
        if execStr is None:
            echo0("* Exec is None so choosing app...")
            return self._choose_app(self.path)
            # ^ Open the file itself since it is *not* in .blnk format.
            #   (Not XDG, but see [The XDG desktop file spec alludes to
            #   Directory as a Type of desktop file but doesn't define a
            #   standard for
            #   it.](gitlab.freedesktop.org/xdg/xdg-utils/-/issues/210)
        else:
            # exec_parts = shlex.split(execStr)
            # ^ Do *not* use (removes backslashes on Windows)
            # if source_key == 'Path':  # comment since if Directory, run it
            if self.get("Type") == "File":
                # execStr = not_quoted(execStr, key=source_key)
                # execStr = exec_parts[0]  # removes backslashes
                # if len(exec_parts) > 1:
                #     raise ValueError("Extra parts (expected file for Exec,"
                #                      " but got: {})".format(exec_parts))
                echo0("* Type={} so choosing app...".format(Type))
                # RETURN EARLY for file
                return self._choose_app(execStr)
        # else only Run the execStr itself if type is Application!

        # RETURNED already unless neither no Exec nor Type "File"

        # ensure version with quotes etc. isn't used:
        # del execStr

        # - However, _run detects Type=Directory and handles that.
        # echo0("Trying _run...")
        cwd, PathErr = self.getExec(key='Path')
        # ^ Resolves relative paths, but also adds quotes, so:
        cwd = not_quoted(cwd)
        if PathErr is not None:
            echo0(PathErr)
        else:
            echo1("* there is no PathErr from getExec(key='cwd') in run.")
            echo1('  - cwd="{}"'.format(cwd))

        # Type is "Application" or "Directory" if we didn't return yet,
        #   usually (neither missing Exec nor is Type "File").
        #   - _run should split parts (for relative, see getExec)
        #     *only if* Type is "Application"
        #   - Type is detected automatically.
        return BLink._run(execStr, self.get('Type'), cwd=cwd)


dtLines = [
    "[Desktop Entry]",
    "Exec={}".format(myBinPath),
    "MimeType=text/blnk;",
    "NoDisplay=true",
    "Name=blnk",
    "Type=Application",
]
'''
^ dtLines is for generating an XDG desktop file for launching blnk itself so
  that blnk appears in the "Choose Application" menu for opening a .blnk file,
  and doesn't represent the content of a .blnk file itself (though blnk format
  is based on the XDG desktop shortcut format).
'''
#
#   Don't set NoDisplay:true or it can't be seen in the "Open With" menu
#   such as in Caja (MATE file explorer)
#   - This is for blnk itself. For blnk files, see blnk_spec.py.


def usage(parser=None):
    # if parser:
    #     parser.print_help()  # prints the full help screen
    print(__doc__, file=sys.stderr)
    if parser:
        parser.print_usage(file=sys.stderr)  # prints only usage


def create_icon(dtPath):
    print("* checking for \"{}\"".format(dtPath))
    if not os.path.isfile(dtPath):
        print("* writing \"{}\"...".format(dtPath))
        if not os.path.isdir(sysdirs['SHORTCUTS']):
            os.makedirs(sysdirs['SHORTCUTS'])
        with open(dtPath, 'w') as outs:
            for line in dtLines:
                outs.write(line + "\n")
        if platform.system != "Windows":
            print("  - installing...")
            iconCommandParts = ["xdg-desktop-icon", "install",
                                "--novendor"]
            cmdParts = iconCommandParts + [dtPath]
            try:
                BLink._run_parts(cmdParts)
            except subprocess.CalledProcessError:
                # os.remove(dtPath)
                # ^ Force automatically recreating the icon.
                echo0("{} failed.".format(cmdParts))
                echo0(str(cmdParts))


def run_file(path, enable_gui=True):
    '''Run a blnk file.
    Args:
        enable_gui (bool, optional): Try to show a tk messagebox for
            errors if True. Defaults to True.

    Returns:
        int: 0 if OK, otherwise there was an error.
    '''
    try:
        link = BLink(path, blnk_format_only=False)
        # ^ This path is the blnk file, not its target.
        # if link.path:
        #     link.run()
        # else it is not recognized blnk format (constructor runs load,
        # and in that case, load runs _choose_app)!
        # ^ init and run are in the same context in case construct
        #   fails.
        # New way:
        if link.is_blnk():
            link.run()
        # else load already ran _choose_app
        return 0
    except FileTypeError:
        pass
        # already handled by Blink
    except FileNotFoundError as ex:
        # echo0(get_traceback())
        # msg = "The file was not found: {} {}".format(ex, get_traceback())
        # msg = get_traceback()
        # ^ Too long, has all lines of traceback, so:
        msg = "{}: {}".format(type(ex).__name__, ex)
        # ^ str(ex) already has path
        showMsgBoxOrErr(
            msg,
            enable_gui=enable_gui,
        )
    except Exception:
        # This case ensures something is shown on the GUI *always*
        #   since main may be run by a script associated with the
        #   blnk filetype in the GUI.
        # msg = "Run couldn't finish: {}".format(ex)
        # msg = "{}: {}".format(type(ex).__name__, ex)
        msg = get_traceback()  # Show all lines since it isn't handled
        showMsgBoxOrErr(
            msg,
            enable_gui=enable_gui,
        )
    # ^ IF commenting bare Exception, the caller must show output.
    return 1


def name_from_url(url):
    # Same logic is in hierosoft
    if sys.version_info.major >= 3:
        from urllib.parse import urlparse
    else:
        from urlparse import urlparse  # type: ignore
        # , parse_qs
    # parts = url.split('/')
    parseresult = urlparse(url)
    # ^ gets ParseResult(scheme='http', netloc='example.com',
    #   path='/random/folder/path.html', params='', query='', fragment='')
    parts = parseresult.path.split("/")
    if parts[-1].lower().startswith('index.'):
        parts = parts[-1]
    if len(parts) > 2:
        # such as ['Poikilos', 'EnlivenMinetest', 'issues', '431']
        # (from https://github.com/Poikilos/EnlivenMinetest/issues/431)
        if parts[-2] == "issues":
            return "{} issue {}".format(parts[-3], parts[-1])
            # ^ such as "EnlivenMinetest issue 431"
    return None


def required_length(count_min, count_max):
    # See <https://stackoverflow.com/a/4195302>
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not count_min <= len(values) <= count_max:
                msg = (
                    'argument "{f}" requires between'
                    ' {count_min} and {count_max} arguments'.format(
                        f=self.dest,
                        count_min=count_min,
                        count_max=count_max,
                    )
                )
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return RequiredLength


def dump_args(args):
    print("args.blnk={}".format(args.blnk), file=sys.stderr)
    print("args.create_shortcut={}".format(args.create_shortcut),
          file=sys.stderr)
    print("- resulting manually-set members:", file=sys.stderr)
    print("  - args.target={}".format(args.target), file=sys.stderr)
    print("  - args.name={}".format(args.name), file=sys.stderr)
    print("args.terminal={}".format(args.terminal), file=sys.stderr)
    print("args.non_interactive={}".format(args.non_interactive),
          file=sys.stderr)
    print("args.update={}".format(args.update), file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        prog="blnk",
        description=__doc__,
        # add_help=__doc__,
        # usage=__doc__
        formatter_class=argparse.RawTextHelpFormatter,  # allow \n in usage
    )
    # group = parser.add_mutually_exclusive_group()
    # ^ "ValueError: mutually exclusive arguments must be optional"
    #   occurs if shortcut is added to this instead of to parser.
    parser.add_argument(
        "-s",
        "--create-shortcut",
        nargs='+',
        action=required_length(1, 2),
        # action="append",
        # nargs=2,
        # metavar=("target", "name"),  # doesn't work (not set)
        help=("Create a new shortcut (-s <target> or"
              " -s <target> [<Name>"
              " (required only if target is URL, can be full path;"
              " .blnk will be added automatically)])."),
    )
    parser.add_argument('blnk', help="An existing blnk file to run",
                        nargs="?")  # Required if no -s. See `mode =`.

    parser.add_argument("-u", "--update", action='store_true')
    # , default=None)
    parser.add_argument(
        "-y", "--non-interactive", action='store_true',
        help=("Force non-interactive mode (no GUI dialogs nor terminal"
              " input prompt if information is incorrect or missing).")
    )
    # or action=argparse.BooleanOptionalAction (Python 3.9)
    parser.add_argument("-c", "--terminal",
                        help=("The target is a console application"
                              " (or should run in a terminal using"
                              " Terminal=true in the blnk file regardless)."))
    # NOTE: Use -c since -t means something else with ln
    # (--target-directory=DIRECTORY)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose")
    group.add_argument("-V", "--debug")

    args = parser.parse_args()
    args.target = None
    args.name = None
    if args.create_shortcut:
        if not isinstance(args.create_shortcut, (list, tuple)):
            raise NotImplementedError(
                "Expected list or tuple. Argument parser is configured wrong.")
        args.target = args.create_shortcut[0]
        if len(args.create_shortcut) > 1:
            args.name = args.create_shortcut[1]
        else:
            args.name = None
    elif not args.blnk:
        raise NotImplementedError(
            "Expected create_shortcut or blnk. Argument parser is set wrong.")
        # return 1

    MODE_RUN = "run"
    MODE_CS = "create shortcut"
    MODE_UPDATE = "update shortcut"
    options = {}
    enable_gui = not args.non_interactive
    options["Terminal"] = "true" if args.terminal else "false"
    # NOTE: verbosity = 2  # 2 to mimic Python 3 logging default WARNING==30
    if args.verbose:
        set_verbosity(3)
    elif args.debug:
        set_verbosity(4)
    if args.blnk:
        if args.update:
            mode = MODE_UPDATE
        else:
            mode = MODE_RUN
        if args.terminal:
            showMsgBoxOrErr(
                "--terminal has no effect in {mode} mode. Cancelling."
                .format(mode=mode),
                enable_gui=enable_gui)
            return 1
        if args.target:
            showMsgBoxOrErr(
                "<target> has no effect in {mode} mode. Cancelling."
                .format(mode=mode),
                enable_gui=enable_gui)
            return 1
    else:
        if args.blnk:
            showMsgBoxOrErr(
                "<blnk> has no effect in create mode. Cancelling.",
                enable_gui=enable_gui)
            return 1
        if not args.target:
            showMsgBoxOrErr(
                "<target> is required to create shortcut. Cancelling.",
                enable_gui=enable_gui)
            return 1
        if args.update:
            showMsgBoxOrErr(
                "--update has no effect on --create-shortcut. Cancelling.",
                enable_gui=enable_gui)
            return 1
        mode = MODE_CS
    target = args.target
    shortcut = args.blnk
    if args.name:
        options["Name"] = args.name
    options["Type"] = None
    target_key = 'Exec'
    if mode == MODE_RUN:
        if is_url(shortcut):
            usage(parser=parser)
            error = ("Can't run a URL, and -s was not specified.\n"
                     "Use `blnk -s '<URL>' \"<Title>\"`"
                     "\nto create a URL shortcut.")
            showMsgBoxOrErr(error, enable_gui=enable_gui)
            return 1
        elif os.path.isdir(shortcut):
            usage(parser=parser)
            error = ("Can't run a directory, and -s was not specified."
                     "\nUse `blnk -s <path>`"
                     "\nto create a Directory shortcut.")
            showMsgBoxOrErr(error, enable_gui=enable_gui)
            return 1

        return run_file(shortcut, enable_gui=enable_gui)

    if mode == MODE_UPDATE:
        # Do not check target
        pass
    elif os.path.isdir(target):
        options["Type"] = "Directory"
    elif os.path.isfile(target):
        options["Type"] = "File"
    elif is_url(target):
        if mode == MODE_RUN:
            pass
            # already returned if so
        elif options.get("Terminal"):
            usage(parser=parser)
            error = "A URL should not run in a terminal."
            showMsgBoxOrErr(error, enable_gui=enable_gui)
            return 1
        # if not URL either: See after this case
        options["Type"] = "Link"
        target_key = "URL"
        if options.get('Name') is None:
            options['Name'] = name_from_url(target)
        if options.get('Name') is None:
            echo1("got: {}".format(sys.argv))
            # escaped_path = shlex_quote(target)
            # has_special = escaped_path != "'%s'" % path
            # NOTE: ^ shlex_quote won't work, since & separates the rest
            #   into a different command if using bash!
            amp_msg = ('If the URL has an ampersand, quote the URL\n'
                       ' to prevent the URL from cutting off such as\n'
                       ' if that is not the complete URL you entered'
                       ' (path={}).'
                       ''.format(target))
            showMsgBoxOrErr(
                ('Error: Please provide a name for the shortcut'
                 ' after the URL\n "{}"\n ({}).'.format(target, amp_msg)),
                enable_gui=enable_gui,
            )
            return 1
    if mode == MODE_CS:
        if options["Type"] is None:
            usage()
            showMsgBoxOrErr(
                "Error: The path \"{}\" is not a file, directory, nor URL"
                " (args={}).".format(target, args),
                enable_gui=enable_gui,
            )
            return 1
    if mode == MODE_RUN:
        pass
        # already returned if so
    elif mode in (MODE_CS, MODE_UPDATE):
        # Create shortcut
        # create_icon()
        link = None
        overwrite = False
        if mode == MODE_UPDATE:
            overwrite = True
            try:
                if not shortcut:
                    dump_args(args)
                    logger.fatal("mode={}".format(mode))
                    raise NotImplementedError("shortcut was not set.")
                link = BLink(path=shortcut)
                if not link.path:
                    raise FileNotFoundError("Can only update existing file")
                # else path is only set if load succeeded
                if not link.target_type:
                    raise NotImplementedError("Missing Type after load")
                if not link.target_key:
                    raise NotImplementedError("Missing valid Type after load")
                if not link.target:
                    raise NotImplementedError("Missing target after load")

                # Redo the analyze process
                #   (usually done during set_target during create):
                results = link.analyze_target(
                    None, target_key=target_key, enable_gui=enable_gui)
                error = results.get("error")
                if error:
                    raise RuntimeError(error)
                    return 1
            except Exception as ex:
                error = "{}: {}".format(type(ex).__name__, ex)
                showMsgBoxOrErr(error, enable_gui=enable_gui)
                raise
        else:
            link = BLink(path=None, load=False)
            if not target:
                raise NotImplementedError("target not set")
            results = link.set_target(
                target, options, target_key=target_key,
                enable_gui=enable_gui)
            error = results.get("error")
            if error:
                raise RuntimeError(error)
                return 1
            if not link.path:
                raise NotImplementedError("link path was not generated")
            if not link.target:
                raise NotImplementedError("Missing target after set_target")
            # Note: path *should* be blank if new
            # (determined by set_target if new)! Therefore set shortcut to it:
            shortcut = link.path
        link.save(shortcut, overwrite=overwrite)
    else:
        raise NotImplementedError("The mode \"{}\" is not known."
                                  "".format(mode))
    return 0


if __name__ == "__main__":
    sys.exit(main())
