"""
Module to handle sending error reports.
"""
import os
import roam
import roam.config
import roam.utils
import sentry_sdk


def can_send():
    """
    Return True if allowed to send error reports to the online error service.
    :return: True if allowed
    """
    # TODO Do this better and check if we are in a package.
    if os.environ.get("ROAM_LOCAL_DEV", "F"):
        roam.utils.log("Sending Error Reports: Disabled for local dev")
        return False

    return roam.config.settings.get("online_error_reporting", True)


def init_error_handler():
    print(roam.config.settings)
    if can_send():
        roam.utils.log("Sending Error Reports: Enabled")
        sentry_sdk.init("https://58a98c15c942424ea274243fd37cf3b2@sentry.io/1553649")
    else:
        roam.utils.log("Sending Error Reports: Disabled")


