#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gevent.monkey; gevent.monkey.patch_all()
import gevent
import csv
import requests
import sys


def post_species(scientific, common, labels):
    resp = requests.post('https://birdseye.space/v1/species', json={
        'names': {
            'scientific': scientific.lower(),
            'common': common.lower()
        },
        'labels': [l.lower() for l in labels]
    })
    assert resp.status_code in (200, 201), 'Unexpected code: {}.'.format(
        resp.status_code)


def main(filename):
    print('Importing {}'.format(filename))
    group_singular = {
        'conifers': [
            'conifer', 'plant', 'land plant', 'botany'],
        'reptiles': [
            'reptile', 'animal', 'cold blood', 'cold bloded', 'vertebrate',
            'fauna'],
        'turtles (non-marine)': [
            'turtle', 'animal', 'non-marine', 'cold blood', 'cold bloded',
            'vertebrate', 'fauna'],
        'butterflies': [
            'butterfly', 'animal', 'insect', 'moths and butterflies', 'fauna',
            'invertebrate'],
        'dragonflies': [
            'dragonfly', 'animal', 'insect', 'dragonflies and damseflies',
            'invertebrate', 'fauna'],
        'mammals': [
            'mammal', 'animal', 'warm blood', 'warm blooded', 'vertebrate',
            'fauna'],
        'birds': [
            'bird', 'animal', 'warm blood', 'warm blooded', 'vertebrate',
            'fauna'],
        'amphibians': [
            'amfibian', 'animal', 'vertebrate', 'fauna'],
        'sphingid moths': [
            'sphingid moth', 'moth', 'animal', 'insect', 'invertebrate',
            'fauna', 'moths and butterflies'],
        'bumblebees': [
            'bumblebee', 'bee', 'bees', 'animal', 'insect', 'invertebrate'],
    }
    with open(filename, newline='') as f:
        count = 0
        # "Scientific Name","Common Name","Family","Taxonomic Group"
        for row in csv.reader(f, delimiter=',', quotechar='"'):
            count += 1
            common = row[1]
            if common == 'null':
                common = row[0]
            gevent.spawn(
                post_species, row[0], common,
                [row[2], row[3]] + group_singular[row[3].lower()])
            if count >= 100:
                gevent.wait()
                count = 0
    gevent.wait()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
