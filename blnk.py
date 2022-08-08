#!/usr/bin/env python3
# See __doc__ further down for documentation.
from __future__ import print_function
import sys
import os
import platform
import subprocess
import traceback
import pathlib
import shlex
from datetime import datetime

ENABLE_TK = False
if sys.version_info.major >= 3:
    import tkinter as tk
    # from tkinter import ttk
    from tkinter import messagebox
    ENABLE_TK = True
else:
    import Tkinter as tk
    # import ttk
    import tkMessageBox as messagebox
    ENABLE_TK = True

associations = {
    ".kdb": ["keepassxc"],
    ".kdbx": ["keepassxc"],
    ".pyw": ["python"],
    ".nja": ["ninja-ide", "-p"],  # required for opening project files
    ".csv": ["libreoffice", "--calc"],
    ".csv": ["/usr/bin/flatpak", "run", "--branch=stable", "--arch=x86_64", "--command=libreoffice", "org.libreoffice.LibreOffice", "--calc"],
}
# ^ Each value can be a string or list.
# ^ Besides associations there is also a special case necessary for
#   ninja-ide to change the file to the containing folder (See
#   associations code further down).
settings = {
    "file_type_associations": associations,
}

verbosity = 0

for argI in range(1, len(sys.argv)):
    arg = sys.argv[argI]
    if arg.startswith("--"):
        if arg == "--debug":
            verbosity = 2
        elif arg == "--verbose":
            verbosity = 1


def which(program, more_paths=[]):
    # Jay, & Mar77i. (2017, November 10). Path-Test if executable exists in
    #     Python? [Answer]. Stack Overflow.
    #     https://stackoverflow.com/questions/377017/
    #     test-if-executable-exists-in-python
    import os
    def is_exe(fpath):
        # The fpath param name DIFFERS since it is an inline function.
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath = os.path.split(program)[0]
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in (os.environ["PATH"].split(os.pathsep) + more_paths):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def echo1(*args, **kwargs):
    if verbosity < 1:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def echo2(*args, **kwargs):
    if verbosity < 2:
        return False
    print(*args, file=sys.stderr, **kwargs)
    return True


def get_traceback(indent=""):
    ex_type, ex, tb = sys.exc_info()
    msg = "{}{} {}:\n".format(indent, ex_type, ex)
    msg += traceback.format_exc()
    del tb
    return msg


def view_traceback(indent=""):
    ex_type, ex, tb = sys.exc_info()
    print("{}{} {}: ".format(indent, ex_type, ex), file=sys.stderr)
    traceback.print_tb(tb)
    del tb
    print("", file=sys.stderr)


blnkTemplate = '''Content-Type: text/blnk
Encoding=UTF-8
Type={Type}
Terminal={Terminal}
NoDisplay=true
Name={Name}
Comment=Shortcut generated by 'blnk -s "{Exec}"' (file last_modified={mtime}).
Exec={Exec}
'''

blnkURLTemplate = '''Content-Type: text/blnk
Encoding=UTF-8
Type={Type}
Terminal={Terminal}
NoDisplay=true
Name={Name}
Comment=Open the URL (This was generated by 'blnk -s "{URL}" "{Name}"').
URL={URL}
Icon=folder-remote
'''

'''
^ for blnk files not blnk itself
- for blnk itself, see dtLines.
- This should NOT have the MimeType key, which is used "to indicate the
  MIME Types that an application knows how to handle"
  -<https://specifications.freedesktop.org/desktop-entry-spec
  /desktop-entry-spec-latest.html>
'''

__doc__ = '''
Blnk (pronounced "blink") makes or runs a shortcut to a file or
directory.

The blnk format is (based on the XDG .desktop file format):
{Template}


If you run such a file and blnk runs it in a text editor, the problem
is that the first line must be the Content-Type line shown (It is case
sensitive), and there must not be any blank line before it.


Options:
-s                Create a shortcut to the given file.
--terminal        Specify "Terminal=true" in the blnk file to indicate
                    that the "Exec" file should run in a Terminal.

The following examples assume you've already made a symlink to blnk.py
as ~/.local/bin/blnk (and that ~/.local/bin is in your path--otherwise,
make the symlink as /usr/local/bin/blnk instead. On windows, make a
batch file that runs blnk and sends the parameters to it).

Create a shortcut:
blnk -s %SOME_PATH%

Where %SOME_PATH% is a full path to a blnk file without the
symbols. The new .blnk file will appear in the current working directory
and the name will be the same as the given filename but with the
extension changed to ".blnk".


Run a shortcut:
blnk %SOME_BLNK_FILE%

Where %SOME_BLNK_FILE% is a full path to a blnk file without the
symbols.

'''.format(Template=blnkTemplate)


# - Type is "Directory" or "File"
# - Name may be shown in the OS but usually isn't (from XDG .desktop
#   format).
# - Exec is the path to actually run (a directory or file). Environment
#   variables are allowed (with the symbols shown):
#   - %USERPROFILES%

class FileTypeError(Exception):
    pass

profile = None

# region same as world_clock (Poikilos' fork)
myDirName = "blnk"
AppData = None
local = None
myLocal = None
shortcutsDir = None
replacements = None
username = None
profiles = None
logsDir = None
if platform.system() == "Windows":
    username = os.environ.get("USERNAME")
    profile = os.environ.get("USERPROFILE")
    _unused_ = os.path.join(profile, "AppData")
    AppData = os.path.join(_unused_, "Roaming")
    local = os.path.join(_unused_, "Local")
    share = local
    myShare = os.path.join(local, myDirName)
    shortcutsDir = os.path.join(profile, "Desktop")
    dtPath = os.path.join(shortcutsDir, "blnk.blnk")
    profiles = os.environ.get("PROFILESFOLDER")
    temporaryFiles = os.path.join(local, "Temp")
else:
    username = os.environ.get("USER")
    profile = os.environ.get("HOME")
    local = os.path.join(profile, ".local")
    share = os.path.join(local, "share")
    myShare = os.path.join(share, "blnk")
    if platform.system() == "Darwin":
        # See also <https://github.com/poikilos/world_clock>
        shortcutsDir = os.path.join(profile, "Desktop")
        Library = os.path.join(profile, "Library")
        AppData = os.path.join(Library, "Application Support")
        LocalAppData = os.path.join(Library, "Application Support")
        logsDir = os.path.join(profile, "Library", "Logs")
        profiles = "/Users"
        temporaryFiles = os.environ.get("TMPDIR")
    else:
        # GNU+Linux Systems
        shortcutsDir = os.path.join(share, "applications")
        AppData = os.path.join(profile, ".config")
        LocalAppData = os.path.join(profile, ".config")
        logsDir = os.path.join(profile, ".var", "log")
        profiles = "/home"
        temporaryFiles = "/tmp"
    dtPath = os.path.join(shortcutsDir, "blnk.desktop")
localBinPath = os.path.join(local, "bin")

statedCloud = "owncloud"
myCloud = "owncloud"
if os.path.isdir(os.path.join(profile, "Nextcloud")):
    myCloud = "Nextcloud"

# NOTE: PATH isn't necessary to split with os.pathsep (such as ":", not
# os.sep or os.path.sep such as "/") since sys.path is split already.

# The replacements are mixed since the blnk file may have come from
#   another OS:
substitutions = {
    "%APPDATA%": AppData,
    "$HOME": profile,
    "%LOCALAPPDATA%": local,
    "%MYDOCS%": os.path.join(profile, "Documents"),
    "%MYDOCUMENTS%": os.path.join(profile, "Documents"),
    "%PROFILESFOLDER%": profiles,
    "%USER%": username,
    "%USERPROFILE%": profile,
    "%TEMP%": temporaryFiles,
    "~": profile,
}
# endregion same as world_clock (Poikilos' fork)

def is_url(path):
    path = path.lower()
    endProtoI = path.find("://")
    if endProtoI > 0:
        # TODO: Check for known protocols? Check for "file" protocol?
        return True
    return False


def replace_isolated(path, old, new, case_sensitive=True):
    '''
    Replace old only if it is at the start or end of a path or is
    surrounded by os.path.sep.
    '''
    if case_sensitive:
        if path.startswith(old):
            path = new + path[len(old):]
        elif path.endswith(old):
            path = path[:-len(old)] + new
        else:
            wrappedNew = os.path.sep + new + os.path.sep
            wrappedOld = os.path.sep + old + os.path.sep
            path = path.replace(wrappedOld, wrappedNew)
    else:
        if path.lower().startswith(old.lower()):
            path = new + path[len(old):]
        elif path.lower().endswith(old.lower()):
            path = path[:-len(old)] + new
        else:
            wrappedNew = os.path.sep + new + os.path.sep
            wrappedOld = os.path.sep + old + os.path.sep
            at = 0
            while at >= 0:
                at = path.lower().find(old.lower())
                if at < 0:
                    break
                restI = at + len(old)
                path = path[:at] + new + path[restI:]
    return path


def replace_vars(path):
    for old,new in substitutions.items():
        if old.startswith("%") and old.endswith("%"):
            path = path.replace(old, new)
        else:
            path = replace_isolated(path, old, new)
    return path


def cmdjoin(parts):
    '''
    Join parts of a command. Add double quotes to each part that
    contains spaces.
    - There is no automatic sanitization (escape sequence generation).
    '''
    cmd = ""
    thisDelimiter = ""
    for i in range(len(parts)):
        part = parts[i]
        if " " in part:
            part = '"{}"'.format(part)
        cmd += thisDelimiter + part
        thisDelimiter = " "
    return cmd


def showMsgBoxOrErr(msg,
                    title="Blnk (Python {})".format(sys.version_info.major),
                    try_gui=True):
    # from tkinter import messagebox
    echo0("{}\nusing {}".format(msg, title))
    print("try_gui={}".format(try_gui))
    if not try_gui:
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
tryBinPath = os.path.join(local, "bin", "blnk")
if os.path.isfile(tryBinPath):
    myBinPath = tryBinPath


class BLink:
    '''
    BASES is a list of paths that could contain the directory if the
    directory is a drive letter that is not C but the os is not Windows.
    '''
    NO_SECTION = "\n"
    BASES = [
        os.path.join(profile, myCloud),
        profile,
    ]
    USERS_DIRS = ["Users", "Documents and Settings"]

    def __init__(self, path, assignmentOperator="=",
                 commentDelimiter="#"):
        self.contentType = None
        self.contentTypeParts = None
        self.tree = {}
        self.lastSection = None
        self.path = None
        self.assignmentOperator = assignmentOperator
        self.commentDelimiter = commentDelimiter
        try:
            self.load(path)
        except FileTypeError as ex:
            raise ex

    def splitLine(self, line):
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
                    echo0("* reverting to deprecated ':' operator")
                    i = tmpI
                else:
                    echo0("WARNING: The line contains no '=', but ':'"
                          " seems like a path since it is followed by"
                          " \\ not \\\\")
        if i < 0:
            raise ValueError("The line contains no '{}': `{}`"
                             "".format(self.assignmentOperator,
                                       line))
        ls = line.strip()
        if self.isComment(ls):
            raise ValueError("splitLine doesn't work on comments.")
        if self.isSection(ls):
            raise ValueError("splitLine doesn't work on sections.")
        k = line[:i].strip()
        v = line[i+len(self.assignmentOperator):].strip()
        if self.commentDelimiter in v:
            # if k != "URL":
            echo1("WARNING: `{}` contains a comment delimiter '{}'"
                  " but inline comments are not supported."
                  "".format(line, self.commentDelimiter))
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

    def _pushLine(self, line, row=None, col=None):
        '''
        Keyword arguments
        row -- Show this row (such as line_index+1) in syntax messages.
        col -- Show this col (such as char_index+1) in syntax messages.
        '''
        if row is None:
            if self.lastSection is not None:
                echo0("WARNING: The line `{}` was a custom line not on"
                      " a row of a file, but it will be placed in the"
                      " \"{}\" section which was still present."
                      "".format(line, self.lastSection))
        isContentTypeLine = False
        if self.contentType is None:
            ctOpener = "Content-Type:"
            if line.startswith(ctOpener):
                isContentTypeLine = True
                values = line[len(ctOpener):].split(";")
                for i in range(len(values)):
                    values[i] = values[i].strip()
                value = values[0]
                self.contentType = value
                self.contentTypeParts = values
        if self.contentType != "text/blnk":
            print("* running non-blnk file directly")
            raise FileTypeError(
                "The file must contain \"Content-Type:\""
                " (usually \"Content-Type: text/blnk\")"
                " before anything else, but"
                " _pushLine got \"{}\" (last file: {})"
                "".format(line, self.path)
            )
        if isContentTypeLine:
            return

        trySection = self.getSection(line)
        if self.isComment(line):
            pass
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
                raise ValueError(pre+"_pushLine got an empty section")
            else:
                self.lastSection = section
        else:
            k, v = self.splitLine(line)
            '''
            if k == "Content-Type":
                self.contentType = v
                return
            '''
            section = self.lastSection
            if section is None:
                section = BLink.NO_SECTION
            sectionD = self.tree.get(section)
            if sectionD is None:
                sectionD = {}
                self.tree[section] = sectionD
            sectionD[k] = v

    def load(self, path):
        self.path = path
        try:
            with open(path, 'r') as ins:
                row = 0
                for line in ins:
                    row += 1
                    try:
                        self._pushLine(line, row=row)
                    except FileTypeError as ex:
                        # Do not produce error messages for the bash
                        # script to show in the GUI since this is
                        # recoverable (and expected if plain text files
                        # are associated with blnk.
                        print(str(ex))
                        print("* running file directly...")
                        return self._choose_app(self.path)
                self.lastSection = None
        except UnicodeDecodeError as ex:
            if path.lower().endswith(".blnk"):
                raise ex
            # else:
            # This is probably not a blnk file, so allow
            # the blank Exec handler to check the file extension.
            pass

    def getBranch(self, section, key):
        '''
        Get a tuple containing the section (section name key for
        self.tree) and the value self.tree[section][key]. The reason
        section is returned is in case the key doesn't exist there but
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
        trySection = BLink.NO_SECTION
        section, v = self.getBranch(trySection, key)
        return v

    def getExec(self, key="Exec"):
        trySection = BLink.NO_SECTION
        section, v = self.getBranch(trySection, key)
        if v is None:
            path = self.path
            if path is not None:
                path = "\"" + path + "\""
            msg = ("WARNING: There was no \"{}\" variable in {}"
                   "".format(key, path))
            return None, msg
        elif section != trySection:
            sectionMsg = section
            if section == BLink.NO_SECTION:
                sectionMsg = "the main section"
            else:
                sectionMsg = "[{}]".format(section)
            msg = "WARNING: \"{}\" was in {}".format(key, sectionMsg)
        if v is None:
            return None, msg
        path = v

        if platform.system() == "Windows":
            if v[1:2] == ":":
                if v[2:3] != "\\":
                    raise ValueError(
                        "The third character should be '\\' when the"
                        " 2nd character is ':', but the Exec value was"
                        " \"{}\"".format(v)
                    )

        else:  # Not windows
            if path.startswith("~/"):
                path = os.path.join(profile, path[2:])

            # Rewrite Windows paths **when on a non-Windows platform**:
            # print("  [blnk] v: \"{}\"".format(v))

            if v[1:2] == ":":

                # ^ Unless the leading slash is removed, join will
                #   ignore the param before it (will treat it as
                #   starting at the root directory)!
                # print("  v[1:2]: '{}'".format(v[1:2]))
                if v.lower() == "c:\\tmp":
                    path = temporaryFiles
                    echo1("  [blnk] Detected {} as {}"
                          "".format(v, temporaryFiles))
                elif v.lower().startswith("c"):
                    echo1("  [blnk] Detected c: in {}"
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
                        # print("  [blnk] parts={}".format(parts))
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
                                      " \"{}\"".format(old, profile))
                                path = os.path.join(profile, rel)
                            else:
                                path = profile
                        else:
                            path = profile
                    elif path.lower() == "users":
                        path = profiles
                    else:
                        path = os.path.join(profile, rest)
                        echo0("  [blnk] {} was forced due to bad path:"
                              " \"{}\".".format(path, v))
                else:
                    echo1("Detected drive letter that is not C:")
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
                            print("  [blnk] {} was detected."
                                  "".format(tryPath))
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
                        path = os.path.join(profile, rest)
                        echo0("  [blnk] {} was forced due to bad path:"
                              " \"{}\".".format(path, v))
            else:
                path = v.replace("\\", "/")

        path = replace_vars(path)
        path = replace_isolated(path, statedCloud, myCloud,
                                case_sensitive=False)
        if path != v:
            print("  [blnk] changing \"{}\" to"
                  " \"{}\"".format(v, path))
        return path, None

    @staticmethod
    def _run_parts(parts, check=True):
        print("* running \"{}\"...".format(parts))
        run_fn = subprocess.check_call
        use_check = False
        if hasattr(subprocess, 'run'):
            # Python 3
            use_check = True
            run_fn = subprocess.run
            print("  - using subprocess.run")
            part0 = which(parts[0])
            # if localPath not in os.environ["PATH"].split(os.pathsep):
            if part0 is None:
                part0 = which(parts[0], more_paths=[localBinPath])
                if part0 is not None:
                    parts[0] = part0
        else:
            print("  - using Python 2 subprocess.check_call"
                  " from Python {}"
                  "".format(sys.version_info.major))
            # check_call requires a full path (!):
            if not os.path.isfile(parts[0]):
                part0 = which(parts[0], more_paths=[localBinPath])
                if part0 is not None:
                    parts[0] = part0
        try:
            if use_check:
                run_fn(parts, check=check)
            else:
                run_fn(parts)
        except FileNotFoundError as ex:
            pathMsg = (" (The system path wasn't checked"
                       " since the executable part is a path)")
            if os.path.split(parts[0])[1] == parts[0]:
                # It is a filename not a path.
                pathMsg = (" ({} is not in the system path)"
                           "".format(parts[0]))
            raise FileNotFoundError(
                "Running external application `{}` for a non-blnk file"
                " failed{}:"
                " {}".format(cmdjoin(parts), pathMsg, ex),
            )
        except FileNotFoundError as ex:
            echo0(get_traceback())
            raise FileNotFoundError(
                'The file was not found: '
                ' {} ({})'.format(cmdjoin(parts), ex),
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
        return 0
    @staticmethod
    def _run(Exec, Type):
        '''
        This is a static method, so any object members must be sent.

        Run the correct path automatically using the Type variable from
        the blnk file (Type can be Directory, File, OR Application).
        Note that the "Path" key sets the working directory NOT the
        target, but the Exec argument is equivalent to "Exec".
        '''
        tryCmd = "xdg-open"
        # TODO: try os.popen('open "{}"') on mac
        # NOTE: %USERPROFILE%, $HOME, ~, or such should already be
        #   replaced by getExec.
        this_exists = os.path.isfile
        execParts = shlex.split(Exec)
        if len(execParts) > 1:
            Exec = execParts[0]
        if Type == "Directory":
            this_exists = os.path.isdir
        elif Type == "Application":
            return BLink._run_parts(execParts, check=True)
        if platform.system() == "Windows":
            if (len(Exec) >= 2) and (Exec[1] == ":"):
                if not os.path.exists(Exec):
                    raise FileNotFoundError(
                        "The Exec target doesn't exist: {}"
                        "".format(Exec)
                    )
            os.startfile(Exec, 'open')
            # run_fn('cmd /c start "{}"'.format(Exec))
            return 0
        thisOpenCmd = None
        if not "://" in Exec:
            if not this_exists(Exec):
                raise FileNotFoundError(
                    '"{}"'
                    ''.format(Exec)
                )
        try:
            thisOpenCmd = tryCmd
            print("  - thisOpenCmd={}...".format(thisOpenCmd))
            return BLink._run_parts([thisOpenCmd, Exec], check=True)
        except OSError as ex:
            try:
                echo0(str(ex))
                thisOpenCmd = "open"
                print("  - thisOpenCmd={}...".format(thisOpenCmd))
                return BLink._run_parts([thisOpenCmd, Exec], check=True)
            except OSError as ex2:
                echo0(str(ex2))
                thisOpenCmd = "xdg-launch"
                print("  - trying {}...".format(thisOpenCmd))
                return BLink._run_parts([thisOpenCmd, Exec], check=True)
        except subprocess.CalledProcessError as ex:
            # raise subprocess.CalledProcessError(
            #     "{} couldn't open the Exec target: \"{}\""
            #     "".format(thisOpenCmd, Exec)
            # )
            raise ex
        return 1  # This should never happen.

    def _choose_app(self, path):
        '''
        Choose an application if either it isn't a blnk file at all or
        Type is "File" (only use _run instead of _choose_app if Type is
        Application).
        '''
        global settings
        print("  - choosing app for \"{}\"".format(path))
        app = "geany"
        # If you set blnk to handle unknown files:
        more_parts = []
        orig_app = app
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
        if which(app) is None:
            dotExt = os.path.splitext(path)[1]
            missing_msg = ""
            if len(more_missing) > 0:
                missing_msg = " (and any of: {})".format(more_missing)
            print('    Warning: "{}"{} is missing so {} will open {}.'
                  ''.format(app, missing_msg, orig_app, dotExt))
            app = orig_app
            more_parts = []
        if path.lower().endswith(".nja"):
            path = os.path.split(path)[0]
            # ^ With the -p option, Ninja-IDE will only open a directory
            #   (with or without an nja, but not the nja file directly).
        print("    - app={}".format(app))
        return BLink._run_parts([app] + more_parts + [path])

    def run(self):
        url, err = self.getExec(key="URL")
        if url is not None:
            return BLink._run(url, self.get("Type"))
        execStr, err = self.getExec()
        if err is not None:
            echo0(err)
        if execStr is None:
            # echo0("* Exec is None...")
            # echo0("Trying _choose_app...")
            return self._choose_app(self.path)
        elif self.get("Type") == "File":
            return self._choose_app(execStr)
        # else only Run the execStr if type is Application!
        # echo0("Trying _run...")
        return BLink._run(execStr, self.get("Type"))
        # ^ Type is detected automatically.


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
  that blnk appears in the "Choose Applicaton" menu for opening a .blnk file,
  and doesn't represent the content of a .blnk file itself (though blnk format
  is based on the XDG desktop shorcut format).
'''
#
#   Don't set NoDisplay:true or it can't be seen in the "Open With" menu
#   such as in Caja (MATE file explorer)
#   - This is for blnk itself. For blnk files, see blnkTemplate.


def usage():
    print(__doc__)


def create_icon():
    print("* checking for \"{}\"".format(dtPath))
    if not os.path.isfile(dtPath):
        print("* writing \"{}\"...".format(dtPath))
        if not os.path.isdir(shortcutsDir):
            os.makedirs(shortcutsDir)
        with open(dtPath, 'w') as outs:
            for line in dtLines:
                outs.write(line + "\n")
        if not platform.system == "Windows":
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


def run_file(path, options):
    '''
    Sequential arguments:
    options -- You must at least set:
        'interactive': Try to show a tk messagebox for errors if True.

    Returns:
    If OK return 0, otherwise another int.
    '''
    try:
        link = BLink(path)
        # ^ This path is the blnk file, not its target.
        link.run()
        # ^ init and run are in the same context in case construct
        #   fails.
        return 0
    except FileTypeError:
        pass
        # already handled by Blink
    except FileNotFoundError as ex:
        # echo0(get_traceback())
        showMsgBoxOrErr(
            "The file was not found: {} {}".format(ex, get_traceback()),
            try_gui=options['interactive'],
        )
    except Exception as ex:
        # msg = "Run couldn't finish: {}".format(ex)
        showMsgBoxOrErr(
            get_traceback(),
            try_gui=options['interactive'],
        )
    # ^ IF commenting bare Exception, the caller must show output.
    return 1


def create_shortcut_file(target, options, target_key="Exec"):
    '''
    Sequential arguments:
    options -- Define values for the shortcut using keys that are the same
        names as used in XDG shortcut format. You must at least set:
        'Terminal' (True will be changed to "true", False to "false"), 'Type',
        'interactive': Try to show a tk messagebox for errors if True.
        (Name will be generated from target's ending if None).

    Keyword arguments:
    target_key -- Set this to 'URL' if targtet is a URL.

    Returns:
    If OK return 0, otherwise another int.

    '''
    valid_target_keys = ["Exec", "URL"]
    if target_key not in valid_target_keys:
        raise ValueError("target_key is '{}' but should be among: {}"
                         "".format(target_key, valid_target_keys))
    if options.get('Name') is None:
        if target_key == "URL":
            raise ValueError("You must provide a 'Name' option for a URL.")
        options["Name"] = os.path.splitext(os.path.split(target)[-1])[0]
    newName = options["Name"] + ".blnk"
    newPath = newName
    if options.get('Type') is None:
        raise KeyError("Type is required.")
    if options.get('Terminal') is None:
        raise KeyError(
            'Terminal (with value True, False, "true" or "false" is required'
        )
    if options['Terminal'] is True:
        options['Terminal'] = "true"
    elif options['Terminal'] is False:
        options['Terminal'] = "false"
    # ^ Use the current directory, so do not use the full path.
    mtime = None
    if os.path.isfile(target) or os.path.isdir(target):
        mtime_ts = pathlib.Path(target).stat().st_mtime
        mtime = datetime.fromtimestamp(mtime_ts)
        # ^ stat raises FileNotFoundError if path is not an existing file.
    if target_key == "Exec":
        content = blnkTemplate.format(
            Type=options["Type"],
            Name=options["Name"],
            Exec=target,
            Terminal=options["Terminal"],
            mtime=mtime,
    )
    elif target_key == "URL":
        content = blnkURLTemplate.format(
            Type=options["Type"],
            Name=options["Name"],
            URL=target,
            Terminal=options["Terminal"],
        )
    else:
        raise NotImplementedError("target_key={}".format(target_key))
    # echo0(content)
    if os.path.exists(newPath):
        echo0("Error: {} already exists.".format(newPath))
        return 1
    with open(newPath, 'w') as outs:
        outs.write(content)
    print("* wrote \"{}\"".format(newPath))
    return 0


def main(args):
    # create_icon()
    if len(args) < 2:
        usage()
        raise ValueError(
            "Error: The first argument is the program but"
            " there is no argument after that. Provide a"
            " file path."
        )
    MODE_RUN = "run"
    MODE_CS = "create shortcut"
    mode = MODE_RUN
    path = None
    options = {}
    options["interactive"] = True
    options["Terminal"] = "false"
    for i in range(1, len(args)):
        arg = args[i]
        if arg == "-s":
            mode = MODE_CS
        elif arg == "--terminal":
            options["Terminal"] = "true"
        elif arg in ["--non-interactive", "-y"]:
            options["interactive"] = False
        else:
            if path is None:
                path = arg
            elif options.get('Name') is None:
                options['Name'] = arg
                echo0('Name="{}"'.format(options['Name']))
            else:
                raise ValueError("The option \"{}\" is unknown and the"
                                 " path was already \"{}\""
                                 "".format(arg, path))
    if path is None:
        usage()
        echo0("Error: The path was not set (args={}).".format(args))
        return 1
    options["Type"] = None
    target_key = "Exec"
    if os.path.isdir(path):
        options["Type"] = "Directory"
    elif os.path.isfile(path):
        options["Type"] = "File"
    elif is_url(path):
        options["Type"] = "Link"
        target_key = "URL"
        if options.get('Name') is None:
            showMsgBoxOrErr(
                ('Error: Please provide a name for the shortcut'
                 ' after the URL "{}".'.format(path)),
                try_gui=options["interactive"],
            )
            return 1
    if options["Type"] is None:
        usage()
        showMsgBoxOrErr(
            "Error: The path \"{}\" is not a file or directory"
            " (args={}).".format(path, args),
            try_gui=options["interactive"],
        )
        return 1
    if mode == MODE_RUN:
        return run_file(path, options)
    elif mode == MODE_CS:
        return create_shortcut_file(path, options, target_key=target_key)
    else:
        raise NotImplementedError("The mode \"{}\" is not known."
                                  "".format(mode))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
