# -*- coding: utf-8 -*-
import nose.tools as nt
import birdseye.jobs as jobs


class ImageToObservationTest(object):

    def setup(self):
        self.file_path = 'test-data/monarch-butterfly.jpg'
        self.file_url = 'https://birdseye.space/birdseye.png'

    def teardown(self):
        pass

    @nt.with_setup(setup, teardown)
    def test_file_path_url(self):
        img_args_fp, _ = jobs.gcv_params(self.file_path)
        nt.assert_is_not_none(img_args_fp)

        img_args_url, _ = jobs.gcv_params(self.file_url)
        nt.assert_is_not_none(img_args_url)
        nt.assert_true(img_args_fp.keys() != img_args_url.keys)

    @nt.with_setup(setup, teardown)
    def test_detect_exif_gps(self):
        gps = jobs.detect_exif_gps('test-data/exif-img-gps.jpg')
        nt.assert_is_not_none(gps)
        nt.assert_equal(len(gps), 2)
        # -33.87546081542969, -116.3016196017795
        nt.assert_true(gps[0] + 33.87546 < 0.0001)
        nt.assert_true(gps[1] + 116.30161 < 0.0001)

        gps = jobs.detect_exif_gps(self.file_path)
        nt.assert_is_none(gps)

    @nt.with_setup(setup, teardown)
    def test_conver_poly(self):
        gps = jobs.detect_exif_gps('test-data/exif-img-gps.jpg')
        gps_poly = jobs.make_poly(gps[0], gps[1], 0.00001)
        nt.assert_is_not_none(gps_poly)
        nt.assert_true(gps_poly.startswith('POLYGON('))
