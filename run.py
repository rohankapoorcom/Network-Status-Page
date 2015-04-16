"""
Launcher for the status package.
This has to be run from one level above the package
"""
import json

from status import app, socketio
from status.functions import Plex, ForecastIO, PfSense

import status


def main():
    """
    Loads the configuration from JSON and initializes the necessary modules
    """
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
    except IOError:
        exit('Missing Config File: config.json')

    env = config.get('environment', '')
    if not env:
        exit('Missing environment in config.json')

    config = config.get(env, {})
    if not config:
        exit('Missing configuration in config.json')

    status.config = config
    status.modules['plex'] = Plex(**status.config['plex'])
    status.modules['forecast'] = ForecastIO(**status.config['forecast'])
    status.modules['pfsense'] = PfSense(**status.config['pfsense'])

    socketio.run(app, **status.config['app'])

if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    main()
