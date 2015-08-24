"""
Launcher for the status package.
This has to be run from one level above the package
"""
import json
import os

import status
from status import app, socketio
from status.functions import ForecastIO, PfSense, Plex, Services


def main():
    """
    Loads the configuration from JSON and initializes the necessary modules
    """
    try:
        path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(path, 'config.json')
        with open(config_path, 'r') as config_file:
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
    status.modules['services'] = Services(status.config['services'])

    socketio.run(app, **status.config['app'])

if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    main()
