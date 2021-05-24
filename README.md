# Prometheus Dynamic Exporter
A dynamic metric exporter for Prometheus. Serve your custom metrics via https and basic authenticaiton by adding values in textfiles.

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
```sudo apt-get install python-openssl```
- ### python-configparser
```sudo apt-get install python-configparser```

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
Make the python file executeable (```chmod +x prometheus_dynamic_exporter.py```) and fire it up as **root** user(```sudo ./prometheus_dynamic_exporter.py```).
If you change the port to some value above 1024 you can run it without root privileges.
If everything is good the command should **not** return now. If it does take a look at the logfile which you configured before.

# Check out your metrics
Point your webbrowser to your host where the daemon is running by typing:  https://yourhost/.  
If you are using the self signed certificate you should now see a security warning.  
Click on accept and proceed.  
Now you should see the basic auth popup window asking for your configured username+password you configured already.  
Type in your credentails and proceed. Now you should be able to see your configured metrics.  

# How do I scrape this stuff in Prometheus now ?
Simple. Here is a config example for a Prometheus job_name which will work with your daemon:

```
  - job_name: 'my_first_custom_metrics'
    scrape_interval: 10s
    scrape_timeout: 5s
    static_configs:
        - targets: ['myhostname']
    metrics_path: "/"
    scheme: https
    basic_auth:
      username: 'christian'
      password: 'heavencanwait'
    tls_config:
      insecure_skip_verify: true
```

Make sure to change the hostname in the "targets"-list. Change username+password like you've configured in basic auth before.
Make sure to set the insecure_skip_verify part to true if you are using the self singed certificate. Also notice that the scheme is set to https.

# And now ? Add more metrics !
Just drop more textfiles in your configured metrics directory. Make sure you use the *.metrics* file extension. Inside your .metrics files simply add key values pairs like this:
```
app1_basic_cool_value=4711
app1_basic_other_value=123
app2_basic_mega_value=321
```
and so on...

# Run this as a systemd background service
To run the daemon in the background as a systemd service execute the following steps.
### Move the entire folder to /opt
```mv ....change_this_to_your_path.../prometheus_dynamic_exporter/ /opt/```
### set owner root for the new folder
```chown -R root.root /opt/prometheus_dynamic_exporter/```
### copy the unit file to the systemd service folder
```cp /opt/prometheus_dynamic_exporter/prometheus_dynamic_exporter.service /lib/systemd/system/```
### enable the service
```systemctl enable prometheus_dynamic_exporter.service```
### start the service
```systemctl start prometheus_dynamic_exporter.service```
### check the service status
```systemctl status prometheus_dynamic_exporter.service```
