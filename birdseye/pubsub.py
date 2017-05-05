#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Listens on PubNub channels for observations and pupulates database.
Configuration file is in ~/.pubnub.json and this should look like:

.. code:: Javascript

    {
      "subscribe_key": "demo",
      "publish_key": "demo",
      "channels": ["ch1", "ch2"],
      "channel_groups": ["cg1", "cg2"],
      "ssl": false,
      "reconnect_policy": "linear",
      "publish_channel": "pubch"
    }

'''

import json
import logging
import os.path
import signal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pubnub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener
from pubnub.enums import PNReconnectionPolicy

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


class DebugListener(SubscribeListener):

    def status(self, pubnub, status):
        pass

    def message(self, pubnub, message):
        log.info("Received message: {}".format(json.dumps(message.message)))

    def presence(self, pubnub, presence):
        pass


class ObservationsListener(SubscribeListener):

    def status(self, pubnub, status):
        pass

    def message(self, pubnub, message):
        session = db_session()
        data = message.message
        log.debug("Received message {}".format(json.dumps(data)))
        user = bm.User.find_by_credentials(
            data.get('credentials'), data.get('secret'))
        if user:
            try:
                obs = bm.Observation(
                    user, data.get('geometry'), data.get('media'),
                    data.get('properties'), data.get('species'))
                session.add(obs)
                session.commit()
                session.refresh(obs)
            except Exception as e:
                log.exception(e)
        else:
            log.error("User not found.")

    def presence(self, pubnub, presence):
        pass


class PubSub(object, metaclass=Singleton):

    RECONNECT_POLICY = {
        None: PNReconnectionPolicy.NONE,
        "linear": PNReconnectionPolicy.LINEAR,
        "exponential": PNReconnectionPolicy.EXPONENTIAL,
    }

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
        self.pnconfig.ssl = conf.get("ssl", False)
        rp = PubSub.RECONNECT_POLICY.get("reconnect_policy")
        self.pnconfig.reconnect_policy = rp
        self._channels = conf.get("channels")
        self._chgroups = conf.get("channel_groups")
        self._publish_chan = conf.get("publish_channel")
        self.pubnub = PubNub(self.pnconfig)

    def subscribe(self, listener, channels=None, chgroups=None):
        ch = channels or self._channels
        chg = chgroups or self._chgroups
        if not(ch or chg):
            raise PubSubError("neet channels or groups to subscribe")
        self.pubnub.add_listener(listener)
        p = self.pubnub.subscribe()
        if ch:
            p.channels(ch)
        if chg:
            p.channels(chg)
        return p.execute()

    def unsubscribe_all(self):
        self.pubnub.unsubscribe_all()

    def publish(self, data, meta=None, channel=None):
        # TODO: throttle or queue up messages
        if self.pnconfig.publish_key:
            ch = channel or self._publish_chan
            if ch:
                p = self.pubnub.publish().channel(ch)
                p.message(data)
                if meta:
                    p.meta(meta)
                envelope = p.sync()
                if envelope.status.is_error():
                    raise PubSubError("Error publishing to {}: {}".format(
                        ch, envelope.status.error))
            else:
                raise PubSubError("need publish channel")
        else:
            raise PubSubError("publish key is not configured")


if __name__ == "__main__":
    pubnub.set_stream_logger('pubnub', logging.ERROR)
    pubsub = PubSub()
    pubsub.subscribe(DebugListener())
    # pubsub.subscribe(ObservationsListener())
    print("Pubnub channels subscribed. Listening.\n")
    pubsub.publish({"text": "just published"})
    try:
        signal.pause()
    except:
        pass
    print("Good bye. Listener will exit soon...\n")
    pubsub.unsubscribe_all()
