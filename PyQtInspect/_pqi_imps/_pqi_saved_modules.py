# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/8/18 14:41
# Description:
# ==============================================
import sys
import threading
import time
import socket
import select
import _thread as thread
import queue as _queue

try:
    import xmlrpc.client as xmlrpclib
    import xmlrpc.server as _pydev_SimpleXMLRPCServer
except ImportError:
    # xmlrpc may not be available in some environments
    pass

import http.server as BaseHTTPServer
