#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Listens on PubNub channels for observations and pupulates database.
Configuration file is in ~/.pubnub.json and this should look like:

.. code:: Javascript

    {
      "subscribe_key": "demo",
      "publish_key": "demo",
      "ssl": false OR true,
      "channels": "pubch" OR ["ch1", "ch2"]
    }

'''

from functools import partial
import json
import logging
import os.path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pubnub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from birdseye.default_settings import SQLALCHEMY_DATABASE_URI
import birdseye.models as bm


CONFIG = "~/.pubnub.json"

log = logging.getLogger("pubsub")


def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True)
    Session = sessionmaker(bind=engine)
    return Session()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class PubSubError(RuntimeError):

    pass


class _PubNubPublisher():

    def __init__(self, publisher):
        self.publisher = publisher

    def _proxy(self, method, *args, **kwargs):
        ret = getattr(self.publisher, method)(*args, **kwargs)
        if ret is self.publisher:
            return self
        else:
            return ret

    def __getattr__(self, attr):
        return partial(self._proxy, attr)


class _PubNub():

    def __init__(self, pnconfig):
        self.pubnub = PubNub(pnconfig)

    def publish(self):
        return _PubNubPublisher(self.pubnub.publish())


class PubSub(object, metaclass=Singleton):

    @staticmethod
    def _read_pubnub_config(conffile):
        if isinstance(conffile, str):
            with open(os.path.expanduser(conffile)) as cf:
                return json.load(cf)
        else:
            return json.load(conffile)

    def __init__(self, conffile=CONFIG):
        conf = self._read_pubnub_config(conffile)
        self.pnconfig = PNConfiguration()
        self.pnconfig.subscribe_key = conf.get("subscribe_key")
        if self.pnconfig.subscribe_key is None:
            raise PubSubError("subscribe key is not configured")
        self.pnconfig.publish_key = conf.get("publish_key")
        if self.pnconfig.publish_key is None:
            raise PubSubError("publish key is not configured")
        self.pnconfig.ssl = conf.get("ssl", False)
        self._channels = conf.get("channels")
        self.pubnub = _PubNub(self.pnconfig)

    def publish(self, data, meta=None, channels=None):
        # TODO: throttle or queue up messages
        chs = channels or self._channels
        if isinstance(chs, str):
            chs = [chs]
        elif chs is None:
            raise PubSubError("need publish channel")

        for ch in chs:
            p = self.pubnub.publish().channel(ch)
            p.message(data)
            if meta:
                p.meta(meta)
            envelope = p.sync()
            if envelope.status.is_error():
                raise PubSubError("Error publishing to {}: {}".format(
                    ch, envelope.status.error))


if __name__ == "__main__":
    pubnub.set_stream_logger('pubnub', logging.ERROR)
    pubsub = PubSub()
    pubsub.publish({"text": "just published this!"})
