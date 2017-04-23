# -*- coding: utf-8 -*-
from flask_restful import Resource, Api, representations
import types
from birdseye import app

api = Api(app)
representations.json.settings = {'indent': 4}


def api_route(self, *args, **kwargs):
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper

api.route = types.MethodType(api_route, api)


@api.route('/v1/observations/{observation_id}')
class Sessions(Resource):
    def post(self, credentials):
        return {}


@api.route('/v1/observations/{observation_id}')
class Observation(Resource):

    def get(self, observation_id):
        return []

    def put(self, observation_id):
        return


@api.route('/v1/observations')
class Observations(Resource):

    def get(self):
        return []

    def post(self):
        return


def noqa():
    pass
