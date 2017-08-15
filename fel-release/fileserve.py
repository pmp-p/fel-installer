#!/usr/bin/python3

# -*- coding: utf-8 -*-
import re
import sys

sys.path.insert(0,'./py3')

import argparse
import os

H3I_IMG = os.getenv('H3I_IMG')
ADB = os.getenv('ADB')
if not H3I_IMG:
    print('fatal: H3I_IMG env image filename not set')
    raise SystemExit

if not ADB:
    print('fatal: ADB env adb filename not set')
    raise SystemExit





import sys
import traceback
from inspect import isfunction
from pprint import pprint

from wsgidav import __version__, util
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.wsgidav_app import DEFAULT_CONFIG, WsgiDAVApp
from wsgidav.xml_tools import useLxml

from wsgidav.server.run_server import _get_checked_path, _initConfig, _initCommandLineOptions

import threading

from mpycompat import *

sys.argv.extend( '--host=127.0.0.1 --port=8080 --root=.'.split(' ')  )

sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

DEFAULT_CONFIG_FILE = "wsgidav.conf"
PYTHON_VERSION = "%s.%s.%s" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])


def runCheroot(app, config, mode):
    """Run WsgiDAV using cheroot.server if Cheroot is installed."""
    assert mode == "cheroot"

    try:
        from cheroot import server, wsgi
#         from cheroot.ssl.builtin import BuiltinSSLAdapter
#         import cheroot.ssl.pyopenssl
    except ImportError:
        # if config["verbose"] >= 1:
        print("*" * 78)
        print("ERROR: Could not import Cheroot.")
        print("Try `pip install cheroot` or specify another server using the --server option.")
        print("*" * 78)
        raise

    server_name = "WsgiDAV/%s %s Python/%s" % (
        __version__,
        wsgi.Server.version,
        PYTHON_VERSION)
    wsgi.Server.version = server_name

    # Support SSL
    ssl_certificate = _get_checked_path(config.get("ssl_certificate"))
    ssl_private_key = _get_checked_path(config.get("ssl_private_key"))
    ssl_certificate_chain = _get_checked_path(config.get("ssl_certificate_chain"))
    ssl_adapter = config.get("ssl_adapter", "builtin")
    protocol = "http"
    if ssl_certificate and ssl_private_key:
        ssl_adapter = server.get_ssl_adapter_class(ssl_adapter)
        wsgi.Server.ssl_adapter = ssl_adapter(
            ssl_certificate, ssl_private_key, ssl_certificate_chain)
        protocol = "https"
        if config["verbose"] >= 1:
            print("SSL / HTTPS enabled. Adapter: {}".format(ssl_adapter))
    elif ssl_certificate or ssl_private_key:
        raise RuntimeError("Option 'ssl_certificate' and 'ssl_private_key' must be used together.")
#     elif ssl_adapter:
#         print("WARNING: Ignored option 'ssl_adapter' (requires 'ssl_certificate').")


    if config["verbose"] >= 1:
        print("Running %s" % server_name)
        print("Serving on %s://%s:%s ..." % (protocol, config["host"], config["port"]))

    server_args = {"bind_addr": (config["host"], config["port"]),
                   "wsgi_app": app,
                   "server_name": server_name,
                   }
    # Override or add custom args
    server_args.update(config.get("server_args", {}))

    server = wsgi.Server(**server_args)

    # If the caller passed a startup event, monkey patch the server to set it
    # when the request handler loop is entered
    startup_event = config.get("startup_event")
    if startup_event:
        def _patched_tick():
            server.tick = org_tick  # undo the monkey patch
            if config["verbose"] >= 1:
                print("wsgi.Server is ready")
            startup_event.set()
            org_tick()
        org_tick = server.tick
        server.tick = _patched_tick

    return server

def ABORT(e=None):
    print("ABORT:",e)
    RunTime.wantQuit = True
    try:
        davserver.stop()
    except:
        pass




def davserver_run():
    global davserver
    SUPPORTED_SERVERS = { "cheroot": runCheroot, }
    config = _initConfig()

    app = WsgiDAVApp(config)
    server = config["server"]
    handler = SUPPORTED_SERVERS.get(server)
    if not handler:
        raise RuntimeError("Unsupported server type {!r} (expected {!r})"
                           .format(server, "', '".join(SUPPORTED_SERVERS.keys())))

    if not useLxml and config["verbose"] >= 1:
        print("WARNING: Could not import lxml: using xml instead (slower).")
        print("         Consider installing lxml https://pypi.python.org/pypi/lxml.")

    config["verbose"] = 0

    davserver = handler(app, config, server)
    try:
        davserver.start()
    except KeyboardInterrupt:
        if config["verbose"] >= 1:
            print("Caught Ctrl-C, shutting down...")
        RunTime.wantQuit = True
    finally:
        davserver.stop()
        print('davserver terminated')

def sshadb_run():
    global cmda
    import subprocess
    pro = subprocess.Popen( cmda ,bufsize=0,shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        while not RunTime.wantQuit:
            void = pro.stdout.read(1)
            print( void.decode(), end='', file=sys.stderr )
            sys.stderr.flush()
    except Exception as e:
        ABORT(e)
    finally:
        print('adb link terminated')

def ndb_run():
    global H3I_IMG
    import nbd_server3 as nbd
    try:
        nbd.main(H3I_IMG,9000,'127.0.0.1', offset=4194304)
    except Exception as e:
        ABORT(e)
    finally:
        print('nbd server terminated')

y,my,d,h,m,s = Time.localtime( Time.time() )[:6]
if 0:
    cmd = 'ssh -T -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
    cmd += ' -L127.0.0.1:8266:127.0.0.1:8266 -R127.0.0.1:9000:127.0.0.1:9000 -R127.0.0.1:8080:127.0.0.1:8080'
    cmd += ' -p 2222 root@127.0.0.1 /sbin/bash /data/u-root/fel-initrd/callback.sh'
else:
    cmd = "%s shell /data/u-root/fel-initrd/callback.sh" % ADB
cmda = cmd.split(' ')

benv = []
for k in os.environ:
    if k.startswith('H3I_'):
        benv.append('export %s="%s"' % (k, os.getenv(k) ) )
benv.append('')

benv = '\n'.join(benv)
print("================= BENV ======================")
print(benv,end='')
print("================= /BENV =====================")
import binascii
benv = binascii.b2a_base64( bytes(benv,'utf8') ).decode().strip() + '=='

if 0:
    cmd = """
"%s-%s-%s" "%s:%s:%s" "%s"
""" % (y,my,d,h,m,s, benv )
else:
    fbcon = 'cvbs'
    if not str(os.getenv('H3I_FEX')).count('orangepizero.bin'):
        fbcon = 'fbcon'
    cmd = """
%s-%s-%s %s:%s:%s "%s" "%s"
""" % (y,my,d,h,m,s, benv, fbcon )


cmda.append( cmd.strip() )

print("================ ADB ================")
print(' '.join(cmda) )
print("================ /ADB ===============")
#raise SystemExit


davserver_thr = threading.Thread(target=davserver_run, args=[])
davserver_thr.daemon = True
davserver_thr.start()

sshadb_thr =  threading.Thread(target=sshadb_run, args= [] )
sshadb_thr.daemon = True
sshadb_thr.start()

nbd_thr = threading.Thread(target=ndb_run, args=[])
nbd_thr.daemon = True
nbd_thr.start()

if 1:
    try:
        while not RunTime.wantQuit:
            try:
                Time.sleep(.01)
            except KeyboardInterrupt:
                ABORT('KeyboardInterrupt')
    except Exception as e:
        ABORT(e)
    finally:
        print('bye')
    raise SystemExit
else:
    Time.sleep(2)
    print('Waiting for websocket control channel')
    for x in range(0,11):
        print('.',end='')
        sys.stdout.flush()
        Time.sleep(1)
    exec( compile(open('insert_coin.py').read(), 'insert_coin', 'exec'), globals() ,locals() )











#
