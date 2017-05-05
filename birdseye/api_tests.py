# -*- coding: utf-8 -*-
import nose.tools as nt
import json

from birdseye import app

nt.assert_equal.__self__.__class__.maxDiff = None


class BirdsEyeClient(object):
    def __init__(self, client):
        self.client = client
        self.headers = {}

    def get(self, url):
        return self.client.get(
            url, headers=self.headers, follow_redirects=True)

    def delete(self, url):
        return self.client.delete(
            url, headers=self.headers, follow_redirects=True)

    def post(self, url, data_dict={}):
        return self.client.post(
            url, data=json.dumps(data_dict), headers=self.headers,
            follow_redirects=True, content_type='application/json')

    def put(self, url, data_dict):
        return self.client.put(
            url, data=json.dumps(data_dict), headers=self.headers,
            follow_redirects=True, content_type='application/json')

    def set_authorization(self, secret):
        self.headers['Authorization'] = 'Bearer {}'.format(secret)

    def clear_authorization(self):
        if 'Authorization' in self.headers:
            del self.headers['Authorization']


def assert_error(code, response):
    nt.assert_equal(response.status_code, code)
    nt.assert_equal(response.content_type, 'application/json')
    jr = json.loads(response.get_data(as_text=True))
    nt.assert_equal(jr['status'], 'error')
    nt.assert_is_not_none(jr['message'])
    return jr


def assert_ok(code, response):
    content_type = response.content_type
    status = response.get_data(as_text=True)
    jr = None
    if content_type == 'application/json':
        jr = json.loads(status)
        status = ' '.join([
            m for m in [jr['status'], jr.get('message')] if m is not None])
    nt.assert_equal(
        '{} {} {}\n'.format(response.status_code, content_type, status),
        '{} application/json success\n'.format(code))
    return jr


class UserTest(object):
    def setup(self):
        self.client = BirdsEyeClient(app.test_client())
        self.client.delete('/v1/sessions')
        self.client.delete('/v1/observations')
        self.client.delete('/v1/users')

    def teardown(self):
        pass

    @nt.with_setup(setup, teardown)
    def test_create_user(self):
        resp = assert_ok(201, self.client.post('/v1/users', {
            'credentials': {'email': 'joe@example.com'},
            'secret': '12345',
        }))
        nt.assert_equal(resp['count'], '1')
        nt.assert_equal(len(resp['data']), 1)
        nt.assert_is_not_none(resp['data'][0])

    @nt.with_setup(setup, teardown)
    def test_delete_all_users(self):
        self.client.delete('/v1/users')
        resp = assert_ok(200, self.client.get('/v1/users'))
        nt.assert_equal(resp['count'], '0')
        nt.assert_equal(resp['data'], [])

        resp = assert_ok(201, self.client.post('/v1/users', {
            'credentials': {'email': 'joe@example.com'},
            'secret': '12345',
        }))
        nt.assert_equal(resp['count'], '1')

        self.client.delete('/v1/users')


class SessionTest(object):

    def setup(self):
        self.client = BirdsEyeClient(app.test_client())
        self.client.delete('/v1/sessions')
        self.client.delete('/v1/observations')
        self.client.delete('/v1/users')
        assert_ok(201, self.client.post('/v1/users', {
            'credentials': {'email': 'joe@example.com'},
            'secret': '12345',
        }))

    def teardown(self):
        pass

    @nt.with_setup(setup, teardown)
    def test_get_root(self):
        resp = assert_ok(200, self.client.get('/v1'))
        nt.assert_is_not_none(resp['version'])

    @nt.with_setup(setup, teardown)
    def test_get_session(self):
        resp = assert_ok(200, self.client.post('/v1/sessions', {
            'credentials': {'email': 'joe@example.com'},
            'secret': '12345',
            'tokens': {'fcm_token': '123456789'}
        }))
        nt.assert_equal(resp['count'], '1')
        nt.assert_equal(len(resp['data']), 1)
        nt.assert_is_not_none(resp['data'][0])


class SpeciesTest(object):

    def setup(self):
        self.client = BirdsEyeClient(app.test_client())
        self.client.delete('/v1/sessions')
        self.client.delete('/v1/observations')
        self.client.delete('/v1/users')
        self.client.delete('/v1/species')
        assert_ok(201, self.client.post('/v1/species', {
            'names': {'common': 'pidgeon', 'scientific': 'flying rat'},
            'labels': ['bird', 'gray'],
        }))

    def teardown(self):
        pass

    @nt.with_setup(setup, teardown)
    def test_get_species(self):
        resp = assert_ok(200, self.client.get('/v1/species'))
        nt.assert_equal(resp['count'], '1')


class ObservationTest:

    def setup(self):
        self.client = BirdsEyeClient(app.test_client())
        self.client.delete('/v1/sessions')
        self.client.delete('/v1/observations')
        self.client.delete('/v1/users')
        self.client.delete('/v1/species')
        self.client.post('/v1/users', {
            'credentials': {'email': 'joe@example.com'},
            'secret': '12345',
        })
        geometry = 'POLYGON((-81.3 37.2, -80.63 38.04, -80.02 37.49, -81.3 37.2))'  # noqa
        resp = assert_ok(201, self.client.post('/v1/observations', {
            'credentials': {'email': 'joe@example.com'},
            'secret': '12345',
            'geometry': geometry,
            'media': {},
            'properties': {'vision_labels': [(0.99, 'bird'), (0.95, 'blue')]},
        }))
        nt.assert_equal(resp.get('count'), '1')
        self.obs_id = resp.get('data')[0]

    def teardown(self):
        pass

    @nt.with_setup(setup, teardown)
    def test_get_observations(self):
        resp = assert_ok(200, self.client.get('/v1/mapped_observations'))
        nt.assert_equal(resp['count'], '1')
        nt.assert_equal(len(resp['data']), 1)
        nt.assert_equal(resp['data'], resp['features'])
        nt.assert_equal(
            sorted(resp['data'][0].keys()),
            ['created', 'geometry', 'id', 'properties', 'type'])
        nt.assert_equal(
            sorted(resp['data'][0]['properties'].keys()),
            ['login', 'place', 'title', 'vision_labels'])
        nt.assert_equal(
            sorted(resp['data'][0]['geometry'].keys()),
            ['coordinates', 'type'])

    @nt.with_setup(setup, teardown)
    def test_get_mapped_observations(self):
        resp = assert_ok(200, self.client.get('/v1/mapped_observations'))
        nt.assert_equal(resp['count'], '1')

    @nt.with_setup(setup, teardown)
    def test_get_observation(self):
        resp = assert_error(404, self.client.get(
            '/v1/observations/00000000-0000-0000-0000-000000000000'))
        resp = assert_ok(200, self.client.get('/v1/observations/{}'.format(
            self.obs_id)))
        nt.assert_equal(resp['count'], '1')
