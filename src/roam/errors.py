from raven import Client
import roam
import roam.config
import roam.utils


client = Client(
    dsn='http://681cb73fc39247d0bfa03437a9b53b61:114be99c3a8842188ae7e9381d30374a@sentry.kartoza.com/17',
    release=roam.__version__
    )


def can_send():
    """
    Return True if allowed to send error reports to the online error service.
    :return: True if allowed
    """
    return roam.config.settings.get("online_error_reporting", False)


def send_exception(exinfo):
    if can_send():
        roam.utils.info("Sending error report.")
        client.captureException(exinfo)

