# -*- coding: utf-8 -*-
import sqlalchemy
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Text, text, ForeignKey, Table, Column
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from birdseye import db


def set_path_and_utc(db_conn, conn_proxy):
    c = db_conn.cursor()
    c.execute("SET timezone='utc'")
    c.execute('SET search_path=public, contrib;')
    c.close()
sqlalchemy.event.listen(sqlalchemy.pool.Pool, 'connect', set_path_and_utc)


def new_uuid():
    return str(uuid.uuid4())


class CMDR(object):
    '''Created, Modified, Deleted, Replication.'''
    created = db.Column(
        db.DateTime(),
        default=datetime.utcnow,
        nullable=False
    )
    modified = db.Column(
        db.DateTime(),
        default=None,
        onupdate=datetime.utcnow
    )
    deleted = db.Column(
        db.DateTime(),
        default=None,
        onupdate=datetime.utcnow
    )


class User(CMDR, db.Model):
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

    def __init__(self, credentials, secrets, settings=None, social=None):
        self.credentials = credentials
        self.secrets = secrets
        self.settings = settings or {}
        self.social = social or {}

    def as_public_dict(self):
        return {
            'user_id': self.user_id,
            'credentials': self.credentials,
            'settings': self.settings,
            'social': self.social,
        }

    def __repr__(self):
        return '<User %r>' % self.user_id

    @classmethod
    def delete_all(cls):
        return cls.query.delete()

    @classmethod
    def find_all(cls):
        return cls.query.order_by(cls.created)

    @classmethod
    def find_by_id(cls, user_id):
        return cls.query.filter(cls.user_id == user_id).order_by(cls.created)

    @classmethod
    def find_by_credentials(cls, credentials, secrets):
        query = cls.query.filter(
            text('credentials = :credentials and secrets = :secrets'))
        return query.params(
            credentials=credentials, secrets=secrets).order_by(cls.created)


class Session(CMDR, db.Model):
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

    @classmethod
    def delete_all(cls):
        return cls.query.delete()

    @classmethod
    def find_by_id(cls, session_id):
        return cls.query.filter(
            cls.session_id == session_id).order_by(cls.created)


class Species(CMDR, db.Model):
    '''Species table (maps species to labels)'''
    __tablename__ = 'species'
    species_id = db.Column(UUID, primary_key=True, default=new_uuid)
    # scientific, common, etc
    species_names = db.Column(JSONB, nullable=False)
    # label bingo: vision, user, etc
    species_labels = db.Column(JSONB, nullable=False)

    def __init__(self, species_names, species_labels):
        self.species_names = species_names
        self.species_labels = species_labels

    def as_public_dict(self):
        return {
            'species_id': self.user_id,
            'species_names': self.species_names,
            'species_labels': self.species_labels,
        }

    def __repr__(self):
        return '<Species %r>' % self.observation_id

    @classmethod
    def delete_all(cls):
        return cls.query.delete()


class Observation(CMDR, db.Model):
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

    def __init__(self, user, geometry, media, properties=None, species=None):
        self.user_id = user.user_id
        self.user = user
        self.geometry = geometry
        self.media = media
        self.properties = properties or {}
        self.species_id = species.species_id if species else None
        self.species = species

    def as_public_dict(self):
        return {
            'created': self.created,
            'observation_id': self.observation_id,
            'geometry': self.geometry,
            'media': self.media,
            'properties': self.properties,
            'species': self.species.as_public_dict(),
            'author': self.user.social,
        }

    def __repr__(self):
        return '<Observation %r>' % self.observation_id

    @classmethod
    def delete_all(cls):
        return cls.query.delete()


observation_summary = Table(
    'observation_summary', db.Model.metadata,
    Column('left_id', UUID, ForeignKey('left.id')),
    Column('right_id', UUID, ForeignKey('right.id'))
)


class Summary(CMDR, db.Model):
    '''Results of calculations over observations'''
    __tablename__ = 'summaries'
    summary_id = db.Column(UUID, primary_key=True, default=new_uuid)
    # metadata: description, etc.
    properties = db.Column(JSONB, nullable=False)
    geometry = db.Column(Geometry('POLYGON'), nullable=False)

    observations = relationship('Observation', secondary=observation_summary)

    def __init__(self, properties, geometry, observations=None):
        self.properties = properties
        self.geometry = geometry
        self.observations = observations or []

    def as_public_dict(self):
        return {
            'created': self.created,
            'summary_id': self.summary_id,
            'properties': self.properties,
            'geometry': self.geometry,
        }

    def __repr__(self):
        return '<Summary %r>' % self.summary_id

    @classmethod
    def delete_all(cls):
        return cls.query.delete()
