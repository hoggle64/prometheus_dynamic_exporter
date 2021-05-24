#!/usr/bin/python

import BaseHTTPServer, SimpleHTTPServer
from OpenSSL import crypto, SSL
from socket import gethostname
import os
import re
import ssl
import base64
import socket
import configparser
import logging
import time
import sys
import getpass

class prometheus_dynamic_exporter(SimpleHTTPServer.SimpleHTTPRequestHandler):

  def do_AUTHHEAD(self):
    try:
      logging.info('sending auth header')
      self.send_response(401)
      self.send_header('WWW-Authenticate', 'Basic realm=\"Authorize yourself\"')
      self.send_header('Content-Length',0)
      self.send_header('Content-type', 'text/plain')
      self.end_headers()
    except Exception as e:
      logging.error('cannot send authorization header to client.')
      logging.error(repr(e))

  def do_HEAD(self,length, rc):
    try:
      logging.info('sending header')
      self.send_response(rc)
      self.send_header('Content-type', 'text/plain')
      self.send_header('Content-Length',length)
      self.end_headers()
    except Exception as e:
      logging.error('cannot send header to client.')
      logging.error(repr(e))

  def do_user_verify(self, user, password):
    logging.info('user ' + user + ' is trying to authenticate')
    prop_user     = None
    prop_password = None
    try:
      prop_user     = config['basicauth']['user']
      prop_password = config['basicauth']['password']
    except Exception as e:
      logging.error('unable to fetch user and password properties.')
      logging.error(repr(e))
    if user == prop_user and password == prop_password:
      logging.info('authentication successful')
      return True
    else:
      logging.info('authentication failed')
      return False

  def do_get_metrics(self):
    linecount = 0
    filecount = 0
    metrics = {}
    try:
      for dirpath,_,filenames in os.walk(config['global']['metricsdir']):
        for f in filenames:
          if not f.endswith(".metric"):
            continue
          logging.info('scanning file: ' + f)
          filecount += 1
          file = os.path.abspath(os.path.join(dirpath, f))
          with open(file) as f:
            lines = f.readlines()
            for line in lines:
              linecount += 1
              metric = re.split(':|=',line)
              metrics[metric[0]] = metric[1]
    except Exception as e:
      logging.error('error reading metric file(s)')
      logging.error(repr(e))
    return metrics

  def do_GET(self):
    start = time.time()
    if self.headers.getheader('Authorization') == None:
      self.do_AUTHHEAD()
      pass
    else:
      try:
        encoded =  self.headers.getheader('Authorization')
        encoded = re.sub('^(Basic) *', '', encoded)
        data = base64.b64decode(encoded)
        cred = data.split(':')
      except Exception as e:
        logging.error('error parsing credentials out of authorization header')
        logging.error(repr(e))
      if len(cred) != 2 or cred[0] is None or cred[1] is None:
        logging.error('invalid credentials received')
      if self.do_user_verify(cred[0], cred[1]):
        logging.info("user " +  cred[0] + ' successfully authorized')
        path = re.sub(r'^\/','',self.path)
        path = str(path)
        logging.info('requested path: ' + path)
        if not path == '' and not path == 'metrics':
          logging.warn('invalid path requested. dropping request.')
          return 
        metrics = self.do_get_metrics()
        response = ''
        if len(metrics) == 0:
          logging.warn('no metrics found in configured metrics dir(' + config['global']['metricsdir'] + ')')
        for metric in metrics:
          response += metric + ' ' + metrics[metric]
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
    try:
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
    except Exception as e:
      logging.error('error creating key and self signed certificate.')
      logging.error(repr(e))

  try:
    config = configparser.ConfigParser()
    config.read('prometheus_dynamic_exporter.conf')
  except Exception as e:
      logging.error('error parsing configuration file prometheus_dynamic_exporter.conf')
      logging.error(repr(e))
  
  try:
    logging.basicConfig(level=logging.INFO, filename=config['log']['file'], format = '%(asctime)s  %(levelname)-10s> %(message)s')
  except Exception as e:
      logging.error('error initating logging instance')
      logging.error(repr(e))
  
  logging.info('logging initated')
  logging.info('running as user: ' + getpass.getuser())
  if getpass.getuser() != 'root' and int(config['global']['port'] ) <= 1024:
    logging.error('You are trying to bind to a privileged port with a non-root user. This will fail !')

  if not os.path.isfile(config['certificate']['cert_file']) or not os.path.isfile(config['certificate']['key_file']):
    create_self_signed_cert()

  try:
    server = BaseHTTPServer.HTTPServer((config['global']['bindto'], int(config['global']['port'])), prometheus_dynamic_exporter)
    server.socket = ssl.wrap_socket (server.socket, certfile=config['certificate']['cert_file'],keyfile=config['certificate']['key_file'], server_side=True)
  except:
    logging.fatal('fatal error occured while trying to start server on ' + config['global']['bindto'] + ':' + config['global']['port'])
    print 'fatal error occured. check the log.'
    sys.exit(1) 
  
  logging.info('Started httpserver on port ' + config['global']['port'])
  server.serve_forever()

except KeyboardInterrupt:
  logging.info('^C received, shutting down the web server')
  server.socket.close()

