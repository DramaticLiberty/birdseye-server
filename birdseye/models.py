# -*- coding: utf-8 -*-
import sqlalchemy
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Float, Text
from geoalchemy2 import Geometry
from sqlalchemy import or_, and_, between
from sqlalchemy.orm import aliased

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
    '''
    Created, Modified, Deleted, Replication.
    '''
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
    '''
    Users, many are present in the database.
    '''
    user_id = db.Column(UUID, primary_key=True, default=new_uuid)
    # email, telephone, whatever
    credentials = db.Column(JSONB, nullable=False)
    secrets = db.Column(Text)  # pw hash
    # app personal settings
    settings = db.Column(JSONB, nullable=False)
    # public stuff: nick name, social links, etc.
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
        query = cls.query.filter(and_(
            cls.credentials == credentials, cls.secrets == secrets))
        return query.order_by(cls.created)


class Session(CMDR, db.Model):
    '''
    Sessions
    '''
    session_id = db.Column(UUID, primary_key=True, default=new_uuid)
    expires = db.Column(
        db.DateTime(),
        default=datetime.utcnow,
        nullable=False
    )
    user_id = db.Column(UUID)
    tokens = db.Column(JSONB)  # Related tokens (i.e. FCM, bla ba)

    def __init__(self, user_id=None, tokens=None):
        self.user_id = user_id
        self.tokens = tokens or {}

    def as_public_dict(self):
        return {
            'session_id': self.session_id,
            'expires': self.expires,
            'user': self.user.as_public_dict
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


class Observation(CMDR, db.Model):
    '''
    An observation by a user.
    '''
    observation_id = db.Column(UUID, primary_key=True)
    user_id = db.Column(UUID)
    geometry = db.Column(Geometry('POLYGON'), nullable=False)
    properties = db.Column(JSONB, nullable=False)

    def __init__(self, user_id, location):
        self.id = str(uuid.uuid1())
        self.user_id = user_id
        self.location = location

    def __repr__(self):
        return '<Observation %r>' % self.observation_id

    @classmethod
    def delete_all(cls):
        return cls.query.delete()
