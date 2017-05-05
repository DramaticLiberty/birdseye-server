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
    return '{0}-{1}'.format(base, _randstr())


TESTCONFIG = {
    'subscribe_key': 'demo',
    'publish_key': 'demo',
    'ssl': False,
    'reconnect_policy': None,
    'channels': [_make_channel('testChan'), _make_channel('testChan')],
}


def teardown_singleton_pubsub():
    instances = pubsub.Singleton._instances
    if pubsub.PubSub in instances:
        del instances[pubsub.PubSub]


class PubSubMisconfigurationTest(object):

    def setup(self):
        self.conf = TESTCONFIG.copy()

    def teardown(self):
        teardown_singleton_pubsub()

    @nt.with_setup(setup, teardown)
    def test_no_subscribe_key(self):
        del self.conf['subscribe_key']
        with nt.assert_raises(pubsub.PubSubError):
            self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(self.conf)))

    @nt.with_setup(setup, teardown)
    def test_no_publish_key(self):
        del self.conf['publish_key']
        with nt.assert_raises(pubsub.PubSubError):
            self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(self.conf)))

    def test_no_publish_channel(self):
        del self.conf['channels']
        self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(self.conf)))
        with nt.assert_raises(pubsub.PubSubError):
            self.pubsub.publish('foo')


class PubSubTest(object):

    def setup(self):
        self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(TESTCONFIG)))

    def teardown(self):
        pass

    @nt.with_setup(setup, teardown)
    def test_publish_as_configured(self):
        data = _randstr()
        self.pubsub.publish(data)
        #nt.assert_in(data, self.listener.messages)

    @nt.with_setup(setup, teardown)
    def test_publish_custom_channels(self):
        data = _randstr()
        ch = _make_channel('testChan2')
        self.pubsub.publish(data, channels=ch)
        chs = [_make_channel('testChan2'), _make_channel('testChan2')]
        self.pubsub.publish(data, channels=chs)
        #nt.assert_in(data, self.listener.messages)
