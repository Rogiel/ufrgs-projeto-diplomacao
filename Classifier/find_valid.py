#!/usr/bin/env python2

import parser
import matcher
import os
import imp
import utils
from itertools import islice

matchers = {
    'Terran': matcher.BuildOrderMatcher(),
    'Zerg': matcher.BuildOrderMatcher(),
    'Protoss': matcher.BuildOrderMatcher()
}


def list_replays(dir):
    for root, directories, files in os.walk(dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            yield filepath


foo = imp.load_source('TrainingSet.index', 'TrainingSet/index.py')
for (race, builds) in foo.training_set_replays.iteritems():
    for (name, replay_files) in builds.iteritems():

        # skip = int(len(replay_files) * 0.2)
        replay_files_iter = replay_files.iteritems()
        # for i in range(0, skip):
        #     next(replay_files_iter)
        for (replay_file, playerID) in replay_files_iter:
            bos = parser.parse(replay_file, truncate=True)
            player = bos[playerID]
            bo = player['BuildOrder']

            print replay_file, player['Name']

            if player['Race'] != race:
                print 'Invalid race for replay ' + replay_file + '. Given ' + player['Race'] + ', expected ' + race
                exit()
            bo.name = name
            matchers[race].train([bo], name)

for matcher in matchers.itervalues():
    matcher.build_distribution()

matched = dict()
for replay_file in list_replays('Replays/WCS Spring Championship 2016'):
    bos = parser.parse(replay_file, truncate=True)
    for (playerID, bo) in bos.iteritems():
        if bo['Race'] != 'Protoss':
            continue
        results = matchers[bo['Race']].classify(bo['BuildOrder'])
        (probable, p) = utils.get_most_probable_build(results)

        if probable not in matched:
            matched[probable] = dict()
        matched[probable][replay_file] = playerID

print matched

# rates = dict()
# for (race, builds) in foo.training_set_replays.iteritems():
#     for (name, replay_files) in builds.iteritems():
#         if name not in rates:
#             rates[name] = {
#                 'Total': 0,
#                 'OK': 0
#             }
#
#         # skip = int(len(replay_files) * 0.2)
#         # n = 0
#
#         for (replay_file, pid) in replay_files.iteritems():
#             bos = parser.parse(replay_file, truncate=True)
#             for (playerID, bo) in bos.iteritems():
#                 if playerID != pid:
#                     continue
#                 results = matchers[bo['Race']].classify(bo['BuildOrder'])
#                 (probable, p) = utils.get_most_probable_build(results)
#
#                 rates[name]['Total'] += 1
#                 if probable == name:
#                     rates[name]['OK'] += 1
#
#                 print name, "->", probable, p
#             # n += 1
#             # if n == skip:
#             #     break
#
# for (name, rate) in rates.iteritems():
#     print name, float(rate['OK']) / float(rate['Total']), "(" + str(rate['OK']) + "/" + str(rate['Total']) + ")"

# print "Terran:  ", len(matchers['Terran'].training)
# print "Zerg:    ", len(matchers['Zerg'].training)
# print "Protoss: ", len(matchers['Protoss'].training)
