Network Status Page
===================

Designed to monitor an advanced home work with forecast.io, Plex, and pfSense integration.

### Features
---------------
* Responsive web design - for use on desktop and mobile browsers
* Designed using [Bootstrap 3](http://getbootstrap.com/)
* Built with [Flask](http://flask.pocoo.org/)
* Uses SocketIO to provide real-time updates to all connected clients
* Tested on Windows/Linux but should also be compatible with OSX


### Requirements
---------------
* Plex Media Server
* pfSense Firewall with the vnstat package installed
* Forecast.io API key
* Linux server
* Python 2.7

### Optional
---------------


### Usage
---------------
* Download and unzip the [latest build](https://github.com/rohankapoorcom/Network-Status-Page/archive/master.zip)
* Open a terminal and go to the folder where you unzipped the build
* Create a virtualenvironment and use pip to install all of the required packages

	```
	virtualenv venv
	source venv/bin/activate
	pip install -r requirements.txt
	```
* Copy config.template.json to config.json and fill in your configuration details
* Start Network Status Page by executing ```python run.py```

### Inspiration
---------------
* Ryan Christensen's original [Network Status Page](https://github.com/d4rk22/Network-Status-Page) for OSX
	* Ryan's webinterface is really polished and well suited for this task
	* My Network Status Page reimplements his html layout allowing direct usage of his CSS
* Cheerag Patel's [port](https://github.com/cheeragpatel/Network-Status-Page) for Linux