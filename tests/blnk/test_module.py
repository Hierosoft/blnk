#!/usr/bin/env python
import os
import sys

TEST_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
TESTS_DIR = os.path.dirname(TEST_MODULE_DIR)
REPO_DIR = os.path.dirname(TESTS_DIR)
TEST_DATA_DIR = os.path.join(TESTS_DIR, "data")


if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)


from blnk import (  # noqa: E402
    BLink,
    # statedCloud,
)

from blnktestutils import testMatch  # noqa: E402

from hierosoft import sysdirs  # noqa: E402
import hierosoft
print("hierosoft.__file__={}".format(hierosoft.__file__))

print("sysdirs={}".format(sysdirs))
profiles = sysdirs['PROFILESFOLDER']
profile = sysdirs['HOME']
username = sysdirs['USER']
myCloud = sysdirs['CLOUD']

docsBL = BLink(os.path.join(TEST_DATA_DIR, "documents.blnk"))
profBL = BLink(os.path.join(TEST_DATA_DIR, "profile.blnk"))
prosBL = BLink(os.path.join(TEST_DATA_DIR, "profiles.blnk"))
gitsBL = BLink(os.path.join(TEST_DATA_DIR, "git.blnk"))
owncBL = BLink(os.path.join(TEST_DATA_DIR, "owncloud.blnk"))
ddocBL = BLink(os.path.join(TEST_DATA_DIR, "d_documents.blnk"))
noC_BL = BLink(os.path.join(TEST_DATA_DIR, "c_does_not_exist.blnk"))
noD_BL = BLink(os.path.join(TEST_DATA_DIR, "d_does_not_exist.blnk"))


print("")
print("Special folders:")
print("profiles: {}".format(profiles))
print("profile: {}".format(profile))
print("username: {}".format(username))
print("")
print("Substitutions:")
# getExec now returns tuple: (path, error)
testMatch(docsBL.getExec(), (os.path.join(profile, "Documents"), None),
          "getExec")
testMatch(profBL.getExec(), (profile, None), "getExec")
testMatch(prosBL.getExec(), (profiles, None), "getExec")
testMatch(gitsBL.getExec(), (os.path.join(profile, "git"), None), "getExec")
testMatch(owncBL.getExec(), (os.path.join(profile, myCloud), None), "getExec")
myCloudPath = os.path.join(profile, myCloud)
if os.path.isdir(myCloudPath):
    testMatch(ddocBL.getExec(), (os.path.join(myCloudPath, "Documents"), None),
              "getExec {}".format(ddocBL.get('Exec')))
else:
    testMatch(ddocBL.getExec(), (os.path.join(profile, "Documents"), None),
              "getExec")
gone = os.path.join(profile, "this", "path", "does", "not", "exist")
if os.path.exists(gone):
    raise RuntimeError(
        "Uh, for this test to work,"
        " you can't actually have a file"
        " or directory called \"{}\".".format(gone))
testMatch(noC_BL.getExec(), (gone, None), "getExec")
testMatch(noD_BL.getExec(), (gone, None), "getExec")

moreTests = "/home/owner/Desktop/blnk-files.txt"
total = 0
tests = 0
warns = 0
if os.path.isfile(moreTests):
    print("")
    print("Running extended tests ({})...".format(moreTests))
    with open(moreTests, 'r') as ins:
        for rawL in ins:
            line = rawL.strip()
            time_example = "2017-12-15 21:18:37.031776423 -0500"
            # if the list has timestamps such as
            # time_example, remove them:
            parts = line.split(" ")
            if len(parts) >= 3:
                if parts[-1].startswith("-"):
                    if len(parts[-2]) >= 8:
                        if parts[-2][2] == ":" or parts[-2][1] == ":":
                            # There is no need to check for another
                            # colon, but it should be there if the time
                            # format matches time_example.
                            if parts[-3][4] == "-" and parts[-3][7] == "-":
                                line = " ".join(parts[:-3])
                        else:
                            pass
                            # print("  len(\"{}\" < 8".format(parts[-2]))
                    else:
                        pass
                        # print("  len(\"{}\" < 8".format(parts[-2]))
                else:
                    pass
                    # print("  {} doesn't start with \"-\"".format(parts[-1]))
            if len(line) == 0:
                continue
            total += 1
            if not os.path.exists(line):
                print("[tests] There is no \"{}\"".format(line))
                continue
            print("[tests] Testing \"{}\":".format(line))
            tests += 1
            testBL = BLink(line)
            Exec = testBL.getExec()
            if not os.path.exists(Exec):
                print("  [tests] {}: WARNING: \"{}\" did not exist."
                      "".format(line, Exec))
                warns += 1
    print("Ran {} existing extended tests (of {} listed)."
          "".format(tests, total))
    if tests > 0:
        print("  * {} of {} target(s) did not exist."
              "".format(warns, tests))

print("All tests passed.")
