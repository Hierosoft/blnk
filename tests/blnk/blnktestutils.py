def assert_equal(got, correct, tb):
    '''Raise an exception when the compared values do not match.

    Args:
        got (any): Say what the function/method being tested actually
            got.
        correct (any): Say what the function/method should have
            returned.
        tb (str): Set a traceback or short description in a
            human-readable form (such as a method name) for display when
            the check doesn't match.
    '''
    # formerly testMatch, renamed so isn't a test
    if tb is None:
        tb = ""
    else:
        tb = tb + " "
    if got != correct:
        raise AssertionError(
            "{}returned \"{}\" but should have returned \"{}\""
            .format(tb, got, correct)
        )
    else:
        print("* {} {} OK".format(tb, got))
