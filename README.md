# prometheus_dynamic_exporter
A dynamic metric exporter for Prometheus. It serves requests via https and is secured with basic authentication. 

# What is this ?
This python script can be used to easily export simple metrics(key/value). You can then easily "scrape" those metrics to process them with Prometheus. Just put one or more metric files in the configured metrics directory and the daemon process will serve them via https protected with basic auth.

# Why was this developed ?
I was looking for a very simple way to feed different custom metrics easily to Prometheus by just dropping key/value pairs in textfiles inside a directory.

# Requirements
I tested this on Ubuntu 20.04 and Mint 20.1
## Python2 ##
(might work with Python3 with some modifications)
## Python modules  ##
I needed to install 2 additional Python modules. This might be different on your system.
- ### python-openssl
- ### python-configparser

# Getting started
Checkout the repo content to an appropriate directory of your choice.

```git clone https://github.com/hoggle64/prometheus_dynamic_exporter```

Change to the checkout directory

```cd prometheus_dynamic_exporter/```

Open the file ```prometheus_dynamic_exporter.conf``` with an editor of your choice and change the properties to fulfil your needs.

The settings explained in detail:

```
[global]
Global settings go here.
port = The TCP port the daemon should listen on.
metricsdir = The directory where all the metric files are dropped.
You can even create a directory structure with multiple files and dirs.
All files with a .metric-Extension will be processed

[certificate]
If you do not put your own certificates in place(see cert_file and key_file below)
the daemon will create a self signed certificate at startup with the following infomation.
You can always delete the cert_file and key_file and the daemon will recreate it.
cert_file           = Filename of your certificate
key_file            = Filename of your private key
country             = Certificate Information: Country
state               = Certificate Information: State
locality            = Certificate Information: Locality/City
organization        = Certificate Information: Name of your organization
organizational_unit = Certificate Information: Unit inside your organization
years               = Certificate Information: How many years should your certificate be valid

[basicauth]
All exposed metrics are protected via basic authentication and can be retreived only with a valid user and password.
user     = basic auth username
password = basic auth password

[log]
All runtime informations are not written to stdout but written to a logfile which can be configured here.
file = path to your logfile
```
## Start the daemon as root
Make the python file executeable (```chmod +x prometheus_dynamic_exporter.py```) and fire it up(```sudo ./prometheus_dynamic_exporter.py```).
If everything is good the command should *not* return now. If it does take a look at the logfile which you configured before.

# Check out your metrics
Point your webbrowser to your host where the daemon is running by typing:  https://yourhost/.
If you are using the self signed certificate you should now see a security warning. Click on accept and proceed. Now you should see the basic auth popup window asking for your configured username+password you configured already. Type in your credentails and proceed. Now you should be able to see your configured metrics.
