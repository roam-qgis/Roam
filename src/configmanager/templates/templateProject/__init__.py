import getpass

def onProjectLoad():
    """
        Return (False, Message) if project shouldn't be loaded, else return (True, None).
    """

    # We just return True here because it's a demo project.
    return True, None

    # This is what a real onProjectLoad check might look like.
    user = getpass.getuser()
    if user == "nathan.woodrow":
        return True, None
    else:
        return False, "{} is not allow to access this module".format(user)

def ProjectLoaded():
    pass