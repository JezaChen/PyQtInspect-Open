# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2024/9/16 23:22
# Description: Connection-related utilities
# ==============================================

import random
import socket


def find_available_port() -> int:
    """
    Find a random available port number.

    :return: an available port number
    """
    port = random.randint(10000, 60000)
    # check if the port is available
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', port))
        return port
    except:
        return find_available_port()  # try again by recursion
    finally:
        s.close()
