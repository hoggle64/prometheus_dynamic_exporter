#!/usr/bin/python

import BaseHTTPServer, SimpleHTTPServer
from OpenSSL import crypto, SSL
from socket import gethostname
#import subprocess
import os
import re
import ssl
import base64
import socket
import configparser
import logging
import time

class prometheus_dynamic_exporter(SimpleHTTPServer.SimpleHTTPRequestHandler):

  def do_AUTHHEAD(self):
    logging.info('sending auth header')
    self.send_response(401)
    self.send_header('WWW-Authenticate', 'Basic realm=\"Authorize yourself\"')
    self.send_header('Content-Length',0)
    self.send_header('Content-type', 'text/plain')
    self.end_headers()

  def do_HEAD(self,length, rc):
    logging.info('sending header')
    self.send_response(rc)
    self.send_header('Content-type', 'text/plain')
    self.send_header('Content-Length',length)
    self.end_headers()

  def do_user_verify(self, user, password):
    logging.info('user ' + user + ' is trying to authenticate')
    if user == config['basicauth']['user'] and password == config['basicauth']['password']:
      logging.info('authentication successful')
      return True
    else:
      logging.info('authentication failed')
      return False

  def do_get_metrics(self):
    linecount = 0
    filecount = 0
    metrics = {}
    for dirpath,_,filenames in os.walk(config['global']['metricsdir']):
      for f in filenames:
        filecount += 1
        file = os.path.abspath(os.path.join(dirpath, f))
        with open(file) as f:
          lines = f.readlines()
          for line in lines:
            linecount += 1
            metric = re.split(':|=',line)
            metrics[metric[0]] = metric[1]
    return metrics

  def do_GET(self):
    start = time.time()
    if self.headers.getheader('Authorization') == None:
      self.do_AUTHHEAD()
      pass
    else:
      encoded =  self.headers.getheader('Authorization')
      encoded = re.sub('^(Basic) *', '', encoded)
      data = base64.b64decode(encoded)
      cred = data.split(':')
      if self.do_user_verify(cred[0], cred[1]):
        logging.info("user " +  cred[0] + ' successfully authorized')
        path = re.sub(r'^\/','',self.path)
        path = str(path)
        metrics = self.do_get_metrics()
        response = ''
        if len(metrics) == 0:
          logging.warn('no metrics found in configured metrics dir(' + config['global']['metricsdir'] + ')')
        for metric in metrics:
          response += metric + '=' + metrics[metric]
        self.do_HEAD(len(response),200)
        self.wfile.write(response)
      else:
        response = "User credential verifcation failed !"
        self.do_HEAD(len(response),403)
        self.wfile.write(response)
      end = time.time()
      logging.info('request processing time: ' + str(round((end-start),4)) + ' seconds')
      pass

  def log_message(self, format, *args):
    logging.info('incoming request: ' + str(args))
    return

try:

  def create_self_signed_cert():
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    cert = crypto.X509()
    cert.get_subject().C  = config['certificate']['country']
    cert.get_subject().ST = config['certificate']['state'] 
    cert.get_subject().L  = config['certificate']['locality'] 
    cert.get_subject().O  = config['certificate']['organization'] 
    cert.get_subject().OU = config['certificate']['organizational_unit']
    if 'common_name' in config['certificate']:
      cn = config['certificate']['common_name']
    else:
      cn = gethostname()
    cert.get_subject().CN = cn
    cert.set_serial_number(999)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(int(config['certificate']['years']) * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha1')
    f = open(config['certificate']['cert_file'], "w")
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    f.close
    f = open(config['certificate']['key_file'], "w")
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    f.close


  config = configparser.ConfigParser()
  config.read('prometheus_dynamic_exporter.conf')

  logging.basicConfig(level=logging.INFO, filename=config['log']['file'], format = '%(asctime)s  %(levelname)-10s> %(message)s')
  logging.info('logging initated')

  if not os.path.isfile(config['certificate']['cert_file']) or not os.path.isfile(config['certificate']['key_file']):
    create_self_signed_cert()

  server = BaseHTTPServer.HTTPServer(('0.0.0.0', int(config['global']['port'])), prometheus_dynamic_exporter)
  server.socket = ssl.wrap_socket (server.socket, certfile=config['certificate']['cert_file'],keyfile=config['certificate']['key_file'], server_side=True)
  logging.info('Started httpserver on port ' + config['global']['port'])
  server.serve_forever()

except KeyboardInterrupt:
  logging.info('^C received, shutting down the web server')
  server.socket.close()

