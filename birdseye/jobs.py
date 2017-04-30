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


def detect_labels(filename_or_url):
    gcv = vision.Client()
    img_args, detect_args = gcv_params(filename_or_url)
    g = gcv.image(**img_args).detect(**detect_args)
    # TODO Raise exception on unsafe media
    return [(vl.score, vl.description) for go in g for vl in go.labels]


def dms_as_float(arc, negative):
    # arc: ((33, 1), (52, 1), (129675, 4096))
    sign = -1 if negative else 1
    return sign * sum(
        (float(arc[i][0]) / float(arc[i][1])) / dms
        for i, dms in enumerate([1.0, 60.0, 3600.0]))


def detect_exif_gps(file_path):
    exif_dict = piexif.load(file_path)
    ifd = 'GPS'
    if ifd not in exif_dict.keys():
        return None
    gps = {piexif.TAGS[ifd][tag]['name']: val
           for tag, val in exif_dict[ifd].items()}
    required = [
        'GPSLatitudeRef', 'GPSLatitude', 'GPSLongitudeRef', 'GPSLongitude']
    if any(gps.get(tag) is None for tag in required):
        return None
    lat = dms_as_float(
        gps['GPSLatitude'], gps['GPSLatitudeRef'] != 'N')
    lon = dms_as_float(
        gps['GPSLongitude'], gps['GPSLongitudeRef'] != 'E')
    return [lat, lon]


def make_poly(lat, lon, radius):
    poly = [(-1.0, 0.0), (0.0, 1.0), (1.0, 0.0), (0.0, -1.0)]
    poly_geo = ', '.join(
        '{} {}'.format(lat + latm * radius, lon + lonm * radius)
        for latm, lonm in poly)
    return 'POLYGON(({}))'.format(poly_geo)


@rq.job
def image_to_observation(file_path, image_url):
    geom = None
    media = {'url': image_url}
    properties = {}
    try:
        latlon = detect_exif_gps(file_path)
        if latlon is None:
            raise ValueError('Image does not have GPS Exif')
        geom = make_poly(latlon[0], latlon[1], 0.000001)
    except:
        pass
    try:
        properties = {'vision_labels': detect_labels(image_url)}
    except:
        pass

    session = db_session()
    obs = bm.Observation(None, geom, media, properties)
    session.add(obs)
    session.commit()
    session.refresh(obs)
