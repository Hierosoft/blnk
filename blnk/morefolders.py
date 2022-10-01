#!/usr/bin/env python
'''
Get platform-specific special folders. This module doesn't use
pathlib, so you can use it without requiring Python 3.4+.

To use it, place morefolders.py in your module and then import it such
as via:

from .morefolders import (
    profile,
    getUnique,
)

Examples:

# To get unique directories for a program named "world_clock":
MY_LUID = "world_clock"  # formerly myDirName
myShare = getUnique(MY_LUID, key="Share:Unique")
dtPath = getUnique(MY_LUID, key="Desktop:Unique")


Known issues:
- [Consider splitting morefolders into a separate repo and require it.
  #5](https://github.com/poikilos/blnk/issues/5)
'''
import sys
import os
import platform


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


profile = None
AppData = None
local = None
# myLocal = None
shortcutsDir = None
replacements = None
username = None
profiles = None
logsDir = None
if platform.system() == "Windows":
    username = os.environ.get("USERNAME")
    profile = os.environ.get("USERPROFILE")
    _data_parent_ = os.path.join(profile, "AppData")
    AppData = os.path.join(_data_parent_, "Roaming")
    local = os.path.join(_data_parent_, "Local")
    share = local
    shortcutsDir = os.path.join(profile, "Desktop")
    profiles = os.environ.get("PROFILESFOLDER")
    temporaryFiles = os.path.join(local, "Temp")
else:
    username = os.environ.get("USER")
    profile = os.environ.get("HOME")
    local = os.path.join(profile, ".local")
    share = os.path.join(local, "share")
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

localBinPath = os.path.join(local, "bin")

# statedCloud = "owncloud"
myCloudName = None
myCloudPath = None

CLOUD_DIR_NAMES = ["Nextcloud", "ownCloud", "owncloud"]

for tryCloudName in CLOUD_DIR_NAMES:
    # ^ The first one must take precedence if more than one exists!
    tryCloudPath = os.path.join(profile, tryCloudName)
    if os.path.isdir(tryCloudPath):
        myCloudName = tryCloudName
        myCloudPath = tryCloudPath
        print('* detected "{}"'.format(myCloudPath))
        break

# NOTE: PATH isn't necessary to split with os.pathsep (such as ":", not
# os.sep or os.path.sep such as "/") since sys.path is split already.

CLOUD_PROFILE = None  # formerly myCloudProfile; such as ~/Nextcloud/profile
# myCloudDir = None

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
    "$CLOUD": None,
    "%CLOUD%": None,
}

# ^ For cloud, see check_cloud.

def check_cloud(cloud_path=None, cloud_name=None):
    '''
    This will check whether there is a "profile" directory in your
    cloud path (such as ~/Nextcloud). It will not modify the global
    detected myCloudPath nor myCloudName (if not present, both are None)
    unless you specify a cloud_path.

    Update the substitutions if the cloud exists or is specified,
    whether or not a "profile" folder exists there.

    Keyword arguments:
    cloud_path -- Set the global myCloudPath. (If None, use the one
        discovered on load, that being any subfolders in Home named
        using any string in the global CLOUD_DIR_NAMES).
    cloud_name -- Set the global cloud name (If None, use the folder
        name of cloud_path if cloud_path was set). This will only be set
        if cloud_path is also set.
    '''
    global CLOUD_PROFILE
    global myCloudPath
    global myCloudName
    if cloud_path is not None:
        myCloudPath = cloud_path
        if cloud_name is not None:
            myCloudName = cloud_name
        else:
            myCloudName = os.path.split(cloud_path)[1]

    if myCloudPath is not None:
        # Update substitutions whether or not the profile path exists:
        if myCloudPath is not None:
            substitutions['%CLOUD%'] = myCloudPath
            substitutions['$CLOUD'] = myCloudPath
        # Set the profile path if it exists:
        tryCloudProfileDir = os.path.join(myCloudPath, "profile")
        if os.path.isdir(tryCloudProfileDir):
            CLOUD_PROFILE = tryCloudProfileDir
        else:
            print('  * Manually create "{}" to enable cloud saves.'
                  ''.format(tryCloudProfileDir))


check_cloud()

non_cloud_warning_shown = False

# Note that the enum module is new in Python 3.4, so it isn't used here.
# class SpecialFolder
# See substitutions for ones implemented as a dictionary or ones not from CLR.


def getUnique(luid, key='Share:Unique', extension=".conf",
        allow_cloud=False):
    '''
    Get a unique path for your program within a special folder. This
    function exists since in some cases, the extension of the file
    depends on the platform.

    A key that is a plural word (before the colon if present) returns a
    directory and singular return a file.

    Sequential arguments:
    luid -- a locally-unique identifier. In other words, this is a name
        that is expected to be unique and not the name of any other
        program. It shouldn't contain spaces or capital letters.

    Keyword arguments:
    key -- Provide a key that is implemented here:
        'Share:Unique': Get your program's path where it may have static
            data.
        'Desktop:Unique': Get your program's platform-specific desktop
            filename. It is your responsibility to create the icon in
            the format designated by the returned file path's extension.
        'Configs:Unique': Get a directory where you can store metadata
            for only your program. You are responsible for creating the
            directory if it doesn't exist. Generally, it is a folder
            within .config (but differs by platform following the
            standards of each platform such as %APPDATA%).
    allow_cloud -- Use the 'Configs:Unique' directory in the cloud,
        but only if a known cloud directory already exists (otherwise
        fall back to 'Configs:Unique' as described.
    '''
    global non_cloud_warning_shown
    if key == 'Share:Unique':
        if platform.system() == "Windows":
            return os.path.join(local, luid)
        else:
            os.path.join(share, luid)
    elif key == 'Desktop:Unique':
        # TODO: Consider using https://github.com/newville/pyshortcuts
        #   to generate shortcut files on Windows/Darwin/Linux.
        if platform.system() == "Windows":
            return os.path.join(shortcutsDir, luid+".blnk")
        elif platform.system() == "Darwin":
            return os.path.join(shortcutsDir, luid+".desktop")
            # TODO: ^ Use ".command", applescript, or something else.
        else:
            return os.path.join(shortcutsDir, luid+".desktop")
    elif key == 'Configs:Unique':
        localUniqueDir = os.path.join(AppData, luid)
        if allow_cloud:
            check_cloud()
            if CLOUD_PROFILE is not None:
                cloudUniqueDir = os.path.join(CLOUD_PROFILE, luid)
                if os.path.isdir(localUniqueDir):
                    if not non_cloud_warning_shown:
                        echo0('Warning: You can merge (then delete) the old'
                              ' "{}" with the new "{}".'
                              ''.format(localUniqueDir, cloudUniqueDir))
                        non_cloud_warning_shown = True
                return cloudUniqueDir
        return localUniqueDir
    else:
        raise NotImplementedError("key='{}'".format(key))


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
    for old, new in substitutions.items():
        if old.startswith("%") and old.endswith("%"):
            path = path.replace(old, new)
        else:
            path = replace_isolated(path, old, new)
    return path


