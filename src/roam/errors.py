from raven import Client
import roam

client = Client(
    dsn='http://681cb73fc39247d0bfa03437a9b53b61:114be99c3a8842188ae7e9381d30374a@sentry.kartoza.com/17',
    release=roam.__version__
    )

def send_exception(exinfo):
    client.captureException(exinfo)

