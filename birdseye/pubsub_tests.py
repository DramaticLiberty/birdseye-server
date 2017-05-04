# -*- coding: utf-8 -*-
from collections import deque
import io
import json

import nose.tools as nt

import birdseye.pubsub as pubsub


TESTCONFIG = {
    "subscribe_key": "demo",
    "publish_key": "demo",
    "ssl": False,
    "reconnect_policy": "linear",
    "channels": ["testChannel1", "testChannel2"],
    "channel_groups": ["testChannelGroup1", "testChannelGroup2"],
    "publish_channel": "testChannel",
}


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
        instances = pubsub.Singleton._instances
        if pubsub.PubSub in instances:
            del instances[pubsub.PubSub]

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
        self.pubsub.subscribe(self.listener, channels=['testChannel'])
        self.pubsub.publish('foo1')
        nt.assert_in('foo1', self.listener.messages)

    @nt.with_setup(setup, teardown)
    def test_no_publish_channel(self):
        del self.conf['publish_channel']
        self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(self.conf)))
        print(">{}<".format(self.pubsub._publish_chan))
        with nt.assert_raises(pubsub.PubSubError):
            self.pubsub.publish('foo')
        self.pubsub.subscribe(self.listener)
        self.pubsub.publish('foo2', channel='testChannel1')
        nt.assert_in('foo2', self.listener.messages)


class PubSubTest(object):

    def setup(self):
        self.pubsub = pubsub.PubSub(io.StringIO(json.dumps(TESTCONFIG)))
        self.listener = _TestListener()

    def teardown(self):
        self.pubsub.unsubscribe_all()

    @nt.with_setup(setup, teardown)
    def test_subscribe_and_publish(self):
        pass
