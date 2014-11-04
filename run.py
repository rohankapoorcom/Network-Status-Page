import json

from status import app
import status

if __name__ == '__main__':
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
    app.run(debug=status.config['debug'], port=status.config['port'])
