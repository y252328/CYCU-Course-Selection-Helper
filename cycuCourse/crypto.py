# -*- coding: utf-8 -*-
"""
CYCU coures selection crypto lib

Version: 1.0.0
"""

import hmac
import hashlib

def crypto(d, f, secureRandom):
    """This function hash password

    Args:
        d (bytes): student id
        f (bytes): password
        secureRandom (bytes): secure random which get from server

    Returns:
        (str, str): ( student id, hashed password )
    """
    m = hashlib.md5()
    m.update(f)
    e = m.hexdigest()
    
    h = hmac.new(e.encode('ascii'), digestmod=hashlib.sha256)
    h.update(d)
    h.update(secureRandom)
    return d.decode('ascii'), h.hexdigest()