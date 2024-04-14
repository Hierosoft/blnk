#!/usr/bin/env python
import os

print("")
print("Starting tests...")

from blnk import (
    BLink,
    profile,
    profiles,
    username,
    statedCloud,
    myCloud,
)


docsBL = BLink(os.path.join("tests", "data", "documents.blnk"))
profBL = BLink(os.path.join("tests", "data", "profile.blnk"))
prosBL = BLink(os.path.join("tests", "data", "profiles.blnk"))
gitsBL = BLink(os.path.join("tests", "data", "git.blnk"))
owncBL = BLink(os.path.join("tests", "data", "owncloud.blnk"))
ddocBL = BLink(os.path.join("tests", "data", "d_documents.blnk"))
noC_BL = BLink(os.path.join("tests", "data", "c_does_not_exist.blnk"))
noD_BL = BLink(os.path.join("tests", "data", "d_does_not_exist.blnk"))


def testMatch(got, correct, tb):
    '''
    Raise an exception when the compared values do not match.

    Sequential arguments:
    got -- Say what the function/method being tested actually got.
    correct -- Say what the function/method should have returned.
    tb -- Set a traceback or short description in a human-readable
          form (such as a method name) for display when the check
          doesn't match.
    '''
    if tb is None:
        tb = ""
    else:
        tb = tb + " "
    if got != correct:
        raise ValueError("{}returned \"{}\" but should have returned \"{}\""
                         "".format(tb, got, correct))
    else:
        print("* {} {} OK".format(tb, got))
print("")
print("Special folders:")
print("profiles: {}".format(profiles))
print("profile: {}".format(profile))
print("username: {}".format(username))
print("")
print("Substitutions:")
testMatch(docsBL.getExec(), os.path.join(profile, "Documents"), "getExec")
testMatch(profBL.getExec(), profile, "getExec")
testMatch(prosBL.getExec(), profiles, "getExec")
testMatch(gitsBL.getExec(), os.path.join(profile, "git"), "getExec")
testMatch(owncBL.getExec(), os.path.join(profile, myCloud), "getExec")
myCloudPath = os.path.join(profile, myCloud)
if os.path.isdir(myCloudPath):
    testMatch(ddocBL.getExec(), os.path.join(myCloudPath, "Documents"), "getExec")
else:
    testMatch(ddocBL.getExec(), os.path.join(profile, "Documents"), "getExec")
gone = os.path.join(profile, "this", "path", "does", "not", "exist")
if os.path.exists(gone):
    raise RuntimeError("Uh, for this test to work, you can't actually have a file or directory called \"{}\".".format(gone))
testMatch(noC_BL.getExec(), gone, "getExec")
testMatch(noD_BL.getExec(), gone, "getExec")

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
                    if len(parts[-2]) >=8:
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
