import re
import sys
import os
import platform
CALLER_NAME = os.path.split(sys.argv[0])[1]
profile = os.environ.get('HOME')
if platform.system() == "Windows":
    profile = os.environ['USERPROFILE']

tryRepo = os.path.join(profile, "git", "moreplatform")
tryModule = os.path.join(tryRepo, "moreplatform")

MY_MODULE = os.path.dirname(os.path.abspath(__file__))
MY_REPO = os.path.dirname(MY_MODULE)
MY_REPOS = os.path.dirname(MY_REPO)

nearbyRepo = os.path.join(MY_REPOS, "moreplatform")


def echo0(*args, **kwargs):  # formerly prerr
    print(*args, file=sys.stderr, **kwargs)


if os.path.isfile(os.path.join(nearbyRepo, "moreplatform", "changes.py")):
    sys.path.insert(0, nearbyRepo)
    echo0("[{}] using nearby {}".format(CALLER_NAME, nearbyRepo))
elif os.path.isdir(tryModule):
    sys.path.insert(0, tryRepo)
    echo0("[{}] using git {}".format(CALLER_NAME, tryRepo))
else:
    pass
    # use the one in the python path (or fail)
    # print("There is no {}".format(os.path.join(thisRepo, "linuxpreinstall")))

try:
    import moreplatform
except ImportError as ex:
    echo0(str(ex))
    echo0('"{}" is a Python module in moreplatform now. You must install the repo:'
          ''.format(CALLER_NAME))
    echo0("# Clone it then:")
    echo0("python3 -m pip install moreplatform")
    echo0('# or just put it in a directory near here such as via:')
    echo0('  git clone https://github.com/hierosoft/moreplatform'
          ' "{}"'.format(nearbyRepo))
    sys.exit(1)
