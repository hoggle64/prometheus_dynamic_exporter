# prometheus_dynamic_exporter
A dynamic metric exporter for Prometheus. It serves requests via https and is secured with basic authentication. 

# What is this ?
This python script can be used to easily export simple metrics(key/value). You can then easily "scrape" those metrics to process them with Prometheus. Just put one or more metric files in the configured metrics directory and the daemon process will serve them via https protected with basic auth.

# Why was this developed ?
I was looking for a very simple way to serve different custom metrics.
