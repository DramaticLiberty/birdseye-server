# -*- coding: utf-8 -*-
'''
Conventions
-----------

* Unless otherwise specified, the response is always a JSON object
* A successful response is always a dictionary with the following keys: \
'status', 'count', 'data' (in this order). Example:

.. code:: Javascript

    {
      "status": "success",
      "count": "1",
      "data": ["AnImportantValue"]
    }

* An error response is always a dictionary with the following keys: \
'status', 'message'. Example:

.. code:: Javascript

    {
      "status": "error",
      "message": "Not Found"
    }

'''
from flask import request
from flask_restful import Resource, Api, representations
import types
import birdseye
from birdseye import app, db
import birdseye.models as bm
import os

api = Api(app)
representations.json.settings = {'indent': 4}


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper

api.route = types.MethodType(api_route, api)


def _success(status_code=200, **message):
    return dict(status='success', **message), status_code


def _success_item(item, status_code=200):
    return _success(status_code=status_code, count='1', data=[item])


def _success_data(data, count, status_code=200):
    return _success(status_code=status_code, count=str(count), data=data)


def _error(message, status_code):
    return dict(status='error', message=message), status_code


def _not_found():
    return _error('Found no matches', 404)


@api.route('/v1')
class Root(Resource):

    def get(self):
        return _success(version=birdseye.__version__)


@api.route('/v1/users')
class Users(Resource):

    def post(self):
        data = request.get_json()
        user = bm.User(data['credentials'], data['secret'])
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return _success_item(user.user_id, status_code=201)

    def get(self):
        # TODO: check admin
        users = bm.User.find_all()
        return _success_data(count=len(users), data=[
            u.as_public_dict() for u in users])

    def delete(self):
        # TODO: check admin
        count = bm.User.delete_all()
        db.session.commit()
        return _success_item(count)


@api.route('/v1/users/<uuid:user_id>')
class User(Resource):

    def get(self, user_id):
        # TODO: check session
        user = bm.User.find_by_id(user_id)
        return _success_item(user.as_public_dict())


@api.route('/v1/sessions')
class Sessions(Resource):

    def post(self):
        data = request.get_json()
        user = bm.User.find_by_credentials(
            data['credentials'], data['secret'])
        if user is None:
            return _error(message='No user.', status_code=403)
        ses = bm.Session(user, data.get('tokens'))
        db.session.add(ses)
        db.session.commit()
        db.session.refresh(ses)
        return _success_item(ses.session_id)

    def delete(self):
        # TODO: Admin
        count = bm.Session.delete_all()
        db.session.commit()
        return _success_item(count)


@api.route('/v1/sessions/<uuid:session_id>')
class Session(Resource):

    def get(self, session_id):
        # TODO: check session
        session = bm.Session.find_by_id(session_id)
        return _success_item(session.as_public_dict())

    def delete(self, session_id):
        # TODO: check session
        count = bm.Session.delete(session_id)
        db.session.commit()
        return _success_item(count)


@api.route('/v1/observations')
class Observations(Resource):

    def get(self):
        # TODO: check admin
        observations = bm.Observation.find_all()
        return _success_data(count=len(observations), data=[
            o.as_public_dict() for o in observations])

    def post(self):
        data = request.get_json()
        user = bm.User.find_by_credentials(
            data.get('credentials'), data.get('secret'))
        if user is None:
            return _error('No user.', 403)
        obs = bm.Observation(user, data.get('geometry'), data.get('media'),
                             data.get('properties'), data.get('species'))
        db.session.add(obs)
        db.session.commit()
        db.session.refresh(obs)
        return _success_item(obs.observation_id, status_code=201)

    def delete(self):
        # TODO: Admin
        count = bm.Observation.delete_all()
        db.session.commit()
        return _success_item(count)


@api.route('/v1/observations/<uuid:observation_id>')
class Observation(Resource):

    def get(self, observation_id):
        # TODO: check_session
        observation = bm.Observation.find_by_id(observation_id)
        if observation:
            return _success_item(observation.as_public_dict())
        else:
            return _not_found()

    def put(self, observation_id):
        return


@api.route('/v1/media')
class Media(Resource):

    def post(self):
        path = request.headers.get('X-File')
        if path is not None:
            ext = 'jpeg'
            basename = '{}.{}'.format(bm.new_uuid(), ext)
            new_path = '/var/www/html/static/{}'.format(basename)
            os.rename(path, new_path)
        else:
            basename = 'not-found.jpg'
        return _success_item('https://birdseye.space/static/{}'.format(
            basename))


@api.route('/v1/species')
class Species(Resource):

    def get(self):
        species = bm.Species.find_all()
        return _success_data(count=len(species), data=[
            s.as_public_dict() for s in species])

    def post(self):
        data = request.get_json()
        species = bm.Species(data.get('names'), data.get('labels'))
        db.session.add(species)
        db.session.commit()
        db.session.refresh(species)
        return _success_item(species.species_id, status_code=201)

    def delete(self):
        count = bm.Species.delete_all()
        db.session.commit()
        return _success_item(count)


def noqa():
    pass
