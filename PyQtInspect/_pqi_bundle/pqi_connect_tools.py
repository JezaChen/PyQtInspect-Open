# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2024/9/16 23:22
# Description: Tools for connecting
# ==============================================

def random_port() -> int:
    """
    Get a random port number
    :return: a valid port number
    """
    import random
    port = random.randint(10000, 60000)
    # check if the port is available
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', port))
        return port
    except:
        return random_port()  # try again by recursion
    finally:
        s.close()