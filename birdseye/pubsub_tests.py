# -*- coding: utf-8 -*-
from collections import deque
import io
import json
import random

import nose.tools as nt

import birdseye.pubsub as pubsub


random.seed()


def _randstr(length=6):
    return '{0:0{length}x}'.format(random.randint(0, 16**length), length=length)


def _make_channel(base):
    return '{0}.{1}'.format(base, _randstr())


TESTCONFIG = {
    'subscribe_key': 'demo',
    'publish_key': 'demo',
    'ssl': False,
    'reconnect_policy': None,
    'channels': [_make_channel('testChan'), _make_channel('testChan')],
    'channel_groups': [_make_channel('testGroup')],
    'publish_channel': _make_channel('testChan')
}


def teardown_singleton_pubsub():
    instances = pubsub.Singleton._instances
    if pubsub.PubSub in instances:
        del instances[pubsub.PubSub]


class _TestListener(pubsub.SubscribeListener):

    def __init__(self):
        super().__init__()
        self.messages = deque()

    def status(self, pubnub, status):
        pass

    def message(self, pubnub, message):
        self.messages.append(message.message)

    def presence(self, pubnub, presence):
        pass


class PubSubMisconfigurationTest(object):

    def setup(self):
        self.conf = TESTCONFIG.copy()
        self.listener = _TestListener()

    def teardown(self):
        if hasattr(self, 'pubsub'):
            self.pubsub.unsubscribe_all()
            del self.pubsub
        teardown_singleton_pubsub()

    @nt.with_setup(setup, teardown)
    def test_no_subscribe_key(self):
        del self.conf['subscribe_key']
        with nt.assert_raises(pubsub.PubSubError):
            self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(self.conf)))

    @nt.with_setup(setup, teardown)
    def test_no_publish_key(self):
        del self.conf['publish_key']
        self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(self.conf)))
        with nt.assert_raises(pubsub.PubSubError):
            self.pubsub.publish('foo')

    @nt.with_setup(setup, teardown)
    def test_no_subscribe_channels(self):
        del self.conf['channels']
        del self.conf['channel_groups']
        self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(self.conf)))
        with nt.assert_raises(pubsub.PubSubError):
            self.pubsub.subscribe(self.listener)

    @nt.with_setup(setup, teardown)
    def test_no_publish_channel(self):
        del self.conf['publish_channel']
        self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(self.conf)))
        with nt.assert_raises(pubsub.PubSubError):
            self.pubsub.publish('foo')


class PubSubTest(object):

    def setup(self):
        self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(TESTCONFIG)))
        self.listener = _TestListener()

    def teardown(self):
        #self.pubsub.unsubscribe_all()
        pass

    @nt.with_setup(setup, teardown)
    def test_subscribe_and_publish_as_configured(self):
        self.pubsub.subscribe(self.listener)
        self.listener.wait_for_connect()
        data = _randstr()
        self.pubsub.publish(data)
        nt.assert_in(data, self.listener.messages)

    @nt.with_setup(setup, teardown)
    def test_subscribe_and_publish_custom_channel(self):
        self.pubsub.subscribe(self.listener)
        data = _randstr()
        ch = _make_channel()
        self.pubsub.subscribe(self.listener, channels=[ch])
        self.listener.wait_for_connect()
        self.pubsub.publish(data, channel=ch)
        nt.assert_in(data, self.listener.messages)
