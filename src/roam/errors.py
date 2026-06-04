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
    if os.environ.get("ROAM_LOCAL_DEV", None):
        roam.utils.log("Sending Error Reports: Disabled for local dev")
        return False

    if not roam.config.settings.get("online_error_reporting", True):
        return False

    dsn = roam.config.settings.get("sentry_dsn", None)
    if not dsn:
        roam.utils.log("Sending Error Reports: No sentry_dsn configured, skipping")
        return False

    return True


def init_error_handler(version):
    if can_send():
        dsn = roam.config.settings.get("sentry_dsn", None)

        # if we have a dsn, then we can initialize sentry and send error reports
        roam.utils.log("Sending Error Reports: Enabled")
        try:
            sentry_sdk.init(
                dsn,
                release=f"Roam@{version}",
                auto_enabling_integrations=False,
            )
        except Exception as e:
            roam.utils.log(f"Sending Error Reports: Failed to initialize sentry: {e}")
    else:
        roam.utils.log("Sending Error Reports: Disabled")