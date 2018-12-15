# coding=utf-8
import requests
from datetime import datetime
import time


def timing():
    while True:
        now = datetime.now()
        hours = [0, 4, 8, 12, 16, 20, 24]
        if now.hour in hours:
            try:
                requests.get('127.0.0.1:80/R9CXjrcx9vNvG8NepiyY13et')
            except:
                pass
            try:
                requests.get('127.0.0.1:5000/R9CXjrcx9vNvG8NepiyY13et')
            except:
                pass
        time.sleep(60 * 60)


timing()
