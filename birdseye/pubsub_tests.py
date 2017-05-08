# -*- coding: utf-8 -*-

import io
import json
import random
from unittest.mock import create_autospec, Mock, patch

from pubnub.pubnub import PubNub
from pubnub.structures import Envelope
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.endpoints.pubsub.publish import Publish

import nose.tools as nt

from birdseye.pubsub import PubSub, PubSubError, Singleton


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
    instances = Singleton._instances
    if PubSub in instances:
        del instances[PubSub]


mockpn = create_autospec(PubNub)
mockenv = Mock()  # Envolpe is a stranger beast
mockstatus = create_autospec(PNStatus)
mockpublish = create_autospec(Publish)

mockpn.publish.return_value = mockpublish
mockpublish.sync.return_value = mockenv
mockenv.status = mockstatus
mockstatus.is_error.return_value = False


class PubSubMisconfigurationTest(object):

    def setup(self):
        self.conf = TESTCONFIG.copy()

    def teardown(self):
        teardown_singleton_pubsub()

    @nt.with_setup(setup, teardown)
    def test_no_subscribe_key(self):
        del self.conf['subscribe_key']
        with nt.assert_raises(PubSubError):
            PubSub(io.StringIO(json.dumps(self.conf)))

    @nt.with_setup(setup, teardown)
    def test_no_publish_key(self):
        del self.conf['publish_key']
        with nt.assert_raises(PubSubError):
            PubSub(io.StringIO(json.dumps(self.conf)))

    def test_no_publish_channel(self):
        del self.conf['channels']
        ps = PubSub(io.StringIO(json.dumps(self.conf)))
        with nt.assert_raises(PubSubError):
            ps.publish('foo')


class PubSubTest(object):

    @patch('birdseye.pubsub.PubNub', mockpn)
    def setup(self, mockpn):
        conf = io.StringIO(json.dumps(TESTCONFIG))
        ps = PubSub(conf)
        mockpn.publish.return_value = mockpublish
        self.mockpn = mockpn

    def teardown(self):
        pass

    @nt.with_setup(setup, teardown)
    def test_publish_as_configured(self):
        data = _randstr()
        nt.set_trace()
        ps.publish(data)
        mockpn.publish.assert_called_once()

    # @nt.with_setup(setup, teardown)
    # def test_publish_custom_channels(self):
    #     data = _randstr()
    #     ch = _make_channel('testChan2')
    #     self.pubsub.publish(data, channels=ch)
    #     chs = [_make_channel('testChan2'), _make_channel('testChan2')]
    #     self.pubsub.publish(data, channels=chs)
        #nt.assert_in(data, self.listener.messages)
