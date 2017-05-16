# -*- coding: utf-8 -*-
import flask.json
import sqlalchemy
import uuid
from datetime import datetime, timedelta
from psycopg2.extensions import AsIs
from psycopg2.extras import Json
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Text, text, ForeignKey, Table, Column
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.ext.declarative import declared_attr
from geoalchemy2 import Geometry

from birdseye import db


def set_path_and_utc(db_conn, conn_proxy):
    c = db_conn.cursor()
    c.execute("SET timezone='utc'")
    c.execute('SET search_path=public, contrib;')
    c.close()


sqlalchemy.event.listen(sqlalchemy.pool.Pool, 'connect', set_path_and_utc)


class DatetimeIS8601JSONEncoder(flask.json.JSONEncoder):

    def __init__(self, **kwargs):
        kwargs['ensure_ascii'] = False
        super().__init__(**kwargs)

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat().rstrip('0')
        if isinstance(obj, AsIs):
            return obj.adapted
        if isinstance(obj, timedelta):
            return obj.days
        return flask.json.JSONEncoder.default(self, obj)


class TimedeltaJSONDecoder(flask.json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        self.hook = kwargs.pop("object_hook", None)
        super().__init__(
            *args, object_hook=self.obj_hook, **kwargs)

    def obj_hook(self, d):
        if isinstance(d, dict):
            if 'duration' in d:
                d['duration'] = timedelta(int(d['duration']))
            return {k: self.obj_hook(v) for k, v in d.items()}
        if (self.hook):
            return self.hook(d)
        return d


def json_dumps(*args, **kwargs):
    # flask.json already has the encoder configured (e.g. for datetime)
    return flask.json.dumps(
        *args, encoding='utf8', cls=DatetimeIS8601JSONEncoder, **kwargs)


def json_loads(*args, **kwargs):
    # flask.json already has the decoder configured (e.g. for timedelta)
    return flask.json.loads(
        *args, encoding='utf8', cls=TimedeltaJSONDecoder, **kwargs)


def PGJson(data):
    return Json(data, dumps=json_dumps),


def new_uuid():
    return str(uuid.uuid4())


class CommonModel(object):
    '''Created, Modified, Deleted, Replication.'''
    # http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/mixins.html

    PUBLIC = ()

    @staticmethod
    def public(*public_col_names):
        ''' Class decorator setting the PUBLIC attribute from:
        - the decorated class attributes whos names are specified as args
        - the PUBLIC attribute of the decorated class
        '''
        def wrap(klass):
            extra = tuple([getattr(klass, a) for a in public_col_names])
            public = getattr(klass, "PUBLIC", ())
            setattr(klass, "PUBLIC", extra + public)
            return klass
        return wrap

    @declared_attr
    def created(cls):
        return db.Column(
            db.DateTime(),
            nullable=False,
            server_default=text("(now() at time zone 'utc')"),
        )

    @declared_attr
    def modified(cls):
        return db.Column(
            db.DateTime(),
            nullable=False,
            server_default=text("(now() at time zone 'utc')"),
            onupdate=text("(now() at time zone 'utc')"),
        )

    @declared_attr
    def deleted(cls):
        return db.Column(
            db.DateTime(),
            server_default=text('NULL'),
        )

    @classmethod
    def delete_all(cls):
        result = cls.query.delete()
        return result

    @classmethod
    def find_all(cls):
        return cls.query.order_by(cls.created).all()

    @classmethod
    def find_by_id(cls, id_):
        return cls.query.get(str(id_))

    def as_public_dict(self):
        return {c.key: getattr(self, c.key) for c in self.PUBLIC}


class DeletableMixin(object):

    def delete(self):
        return self.query.delete()


class User(CommonModel, db.Model):
    '''Users, many are present in the database.'''
    __tablename__ = 'users'
    user_id = db.Column(UUID, primary_key=True, default=new_uuid)
    # email, telephone, whatever
    credentials = db.Column(JSONB, nullable=False)
    secrets = db.Column(Text)  # pw hash
    # app personal settings
    settings = db.Column(JSONB, nullable=False)
    # public stuff: nickname, social links, etc.
    social = db.Column(JSONB)
    PUBLIC = (user_id, credentials, settings, social)

    def __init__(self, credentials, secrets, settings=None, social=None):
        self.credentials = credentials
        self.secrets = secrets
        self.settings = settings or {}
        self.social = social or {}

    def __repr__(self):
        return '<User %r>' % self.user_id

    @classmethod
    def find_by_credentials(cls, credentials, secrets):
        query = cls.query.filter(
            text('credentials = :credentials and secrets = :secrets'))
        query = query.params(
            credentials=PGJson(credentials), secrets=secrets)
        return query.order_by(cls.created).first()


class Session(CommonModel, db.Model, DeletableMixin):
    '''User sessions'''
    __tablename__ = 'sessions'
    session_id = db.Column(UUID, primary_key=True, default=new_uuid)
    expires = db.Column(
        db.DateTime(),
        default=datetime.utcnow,
        nullable=False
    )
    user_id = db.Column(UUID, ForeignKey('users.user_id'))
    # Related tokens (i.e. pubnub_channel, FCM, etc)
    tokens = db.Column(JSONB)

    user = relationship('User')

    def __init__(self, user, tokens=None):
        self.user_id = user.user_id
        self.user = user
        self.tokens = tokens or {}

    def as_public_dict(self):
        return {
            'session_id': self.session_id,
            'expires': self.expires,
            'user': self.user.as_public_dict()
        }

    def __repr__(self):
        return '<Session %r>' % self.session_id


class Species(CommonModel, db.Model):
    '''Species table (maps species to labels)'''
    __tablename__ = 'species'
    species_id = db.Column(UUID, primary_key=True, default=new_uuid)
    # scientific, common, etc
    names = db.Column(JSONB, nullable=False)
    # label bingo: vision, user, etc
    labels = db.Column(JSONB, nullable=False)

    PUBLIC = (species_id, names, labels)

    def __init__(self, names, labels):
        self.names = names
        self.labels = labels

    def __repr__(self):
        return '<Species %r>' % self.observation_id


class Observation(CommonModel, db.Model):
    '''An observation by a user. Timestamped, geostamped, public.'''
    __tablename__ = 'observations'
    observation_id = db.Column(UUID, primary_key=True, default=new_uuid)
    user_id = db.Column(UUID, ForeignKey('users.user_id'))
    geometry = db.Column(Geometry('POLYGON'), nullable=False)
    # photography information: url, license, etc
    media = db.Column(JSONB, nullable=False)
    # meta/descriptive properties: vision labels, user labels, description
    properties = db.Column(JSONB, nullable=False)
    species_id = db.Column(UUID, ForeignKey('species.species_id'))

    user = relationship('User')
    species = relationship('Species')
    geometry_center = column_property(
        geometry.ST_Centroid().ST_AsGeoJSON().cast(JSONB))

    def __init__(self, user, geometry, media, properties=None, species=None):
        self.user_id = user.user_id if user is not None else None
        self.user = user
        self.geometry = geometry
        self.media = media
        self.properties = properties or {}
        self.species_id = species.species_id if species else None
        self.species = species

    def as_public_dict(self):
        return {
            'created': self.created.isoformat(),
            'observation_id': self.observation_id,
            'geometry': repr(self.geometry),
            'media': self.media,
            'properties': self.properties,
            'species': self.species.as_public_dict() if self.species else None,
            'author': self.user.social if self.user is not None else {
                'nickname': 'Unknown'},
        }

    def __repr__(self):
        return '<Observation %r>' % self.observation_id


observation_summary = Table(
    'observation_summary', db.Model.metadata,
    Column('observation_id', UUID, ForeignKey('observations.observation_id')),
    Column('summary_id', UUID, ForeignKey('summaries.summary_id'))
)


@CommonModel.public('created')
class Summary(CommonModel, db.Model):
    '''Results of calculations over observations'''
    __tablename__ = 'summaries'
    summary_id = db.Column(UUID, primary_key=True, default=new_uuid)
    # metadata: description, etc.
    properties = db.Column(JSONB, nullable=False)
    geometry = db.Column(Geometry('POLYGON'), nullable=False)

    observations = relationship('Observation', secondary=observation_summary)

    PUBLIC = (summary_id, properties, geometry)

    def __init__(self, properties, geometry, observations=None):
        self.properties = properties
        self.geometry = geometry
        self.observations = observations or []

    def as_public_dict(self):
        return {
            'created': self.created.isoformat(),
            'summary_id': self.summary_id,
            'properties': self.properties,
            'geometry': repr(self.geometry),
        }

    def __repr__(self):
        return '<Summary %r>' % self.summary_id
