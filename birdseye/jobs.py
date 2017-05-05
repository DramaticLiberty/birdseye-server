# -*- coding: utf-8 -*-
'''
Jobs of all sizes
-----------------

'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.cloud import vision
from google.cloud.vision.feature import Feature
from google.cloud.vision.feature import FeatureTypes
import piexif

from birdseye import rq
import birdseye.models as bm
from birdseye.default_settings import SQLALCHEMY_DATABASE_URI
import birdseye.pubsub as ps


def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True)
    Session = sessionmaker(bind=engine)
    return Session()


def _is_url(filename_or_url):
    return any(filename_or_url.lower().startswith(prefix)
               for prefix in ['http', 'https'])


def gcv_params(filename_or_url):
    detect_args = dict(features=[
        Feature(FeatureTypes.LABEL_DETECTION, 15),
        # Feature(FeatureTypes.SAFE_SEARCH_DETECTION, 2),
    ])
    img_args = dict(source_uri=filename_or_url)
    if not _is_url(filename_or_url):
        img_args = dict(filename=filename_or_url)
    return img_args, detect_args


class NoLabelsDetected(ValueError):
    def __init__(self):
        super().__init__('Failed to detect labels.')


def detect_labels(filename_or_url):
    gcv = vision.Client()
    img_args, detect_args = gcv_params(filename_or_url)
    g = gcv.image(**img_args).detect(**detect_args)
    # TODO Raise exception on NSFW/unsafe media
    return [(vl.score, vl.description) for go in g for vl in go.labels]


def dms_as_float(arc, negative):
    # arc: ((33, 1), (52, 1), (129675, 4096))
    sign = -1 if negative else 1
    return sign * sum(
        (float(arc[i][0]) / float(arc[i][1])) / dms
        for i, dms in enumerate([1.0, 60.0, 3600.0]))


IFD = 'GPS'
GPS_Required = [
    'GPSLatitudeRef', 'GPSLatitude', 'GPSLongitudeRef', 'GPSLongitude']


class NoGPSData(ValueError):
    def __init__(self):
        super().__init__('Image does not have GPS Exif data')


def detect_exif_gps(file_path):
    exif_dict = piexif.load(file_path)
    if IFD not in exif_dict.keys():
        raise NoGPSData()
    gps = {piexif.TAGS[IFD][tag]['name']: val
           for tag, val in exif_dict[IFD].items()}
    try:
        lat = dms_as_float(
            gps['GPSLatitude'], gps['GPSLatitudeRef'] != 'N')
        lon = dms_as_float(
            gps['GPSLongitude'], gps['GPSLongitudeRef'] != 'E')
    except KeyError:
        raise NoGPSData()
    return lat, lon


def make_poly(lat, lon, radius):
    poly = [(-1.0, 0.0), (0.0, 1.0), (1.0, 0.0), (0.0, -1.0), (-1.0, 0.0)]
    poly_geo = ', '.join(
        '{} {}'.format(lat + latm * radius, lon + lonm * radius)
        for latm, lonm in poly)
    return 'POLYGON(({}))'.format(poly_geo)


def make_point(lat, lon):
    return 'POINT({lat} {long})'.format(lat=lat, lon=lon)


@rq.job
def image_to_observation(file_path, image_url):
    geom = None
    media = {'url': image_url}
    properties = {}
    try:
        lat, lon = detect_exif_gps(file_path)
        geom = make_poly(lat, lon, 0.000001)
        labels = [[s, l] for s, l in detect_labels(image_url) if s > 0.55]
        properties = {'vision_labels': labels}
    except Exception as e:
        print(e)
    # add observation to database
    session = db_session()
    obs = bm.Observation(None, geom, media, properties)
    session.add(obs)
    session.commit()
    session.refresh(obs)
    # publish observation to pub-sub channels
    pubsub = ps.PubSub()
    pubsub.publish(obs.as_public_dict())
