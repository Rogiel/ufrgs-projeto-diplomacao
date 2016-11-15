#!/usr/bin/env python2

import parser
import matcher
import os
import imp
import utils
import random
import copy
import collections
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
#
# print ' == SELF-VALIDATION =='
# rates = dict()
#
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
#
# print ' == VALIDATION =='
# rates = dict()
#
validationSet = imp.load_source('ValidationSet.index', 'TrainingSet/validation.py')
# for (race, builds) in validationSet.validation_set_replays.iteritems():
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
#
# for (name, rate) in rates.iteritems():
#     print name, float(rate['OK']) / float(rate['Total']), "(" + str(rate['OK']) + "/" + str(rate['Total']) + ")"

noise_results = dict()

print ' == NOISE TEST =='

for (race, builds) in validationSet.validation_set_replays.iteritems():
    for (name, replay_files) in builds.iteritems():
        if name not in noise_results:
            noise_results[name] = collections.OrderedDict()

        for (replay_file, pid) in replay_files.iteritems():
            bos = parser.parse(replay_file, truncate=True)
            for (playerID, realBO) in bos.iteritems():
                if playerID != pid:
                    continue

                bo = copy.deepcopy(realBO)

                for i in [0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8]:
                    if i not in noise_results[name]:
                        noise_results[name][i] = {
                            'Total': 0,
                            'OK': 0
                        }

                    random.seed(replay_file)

                    length = len(bo['BuildOrder'].actions)
                    to_remove = int(length * i)

                    for r in range(0, to_remove):
                        d = random.randrange(0, len(bo['BuildOrder'].actions))
                        del bo['BuildOrder'].actions[d]

                    results = matchers[bo['Race']].classify(bo['BuildOrder'])
                    (probable, p) = utils.get_most_probable_build(results)

                    noise_results[name][i]['Total'] += 1
                    if probable == name:
                        noise_results[name][i]['OK'] += 1

for (name, rates) in noise_results.iteritems():
    print '\\textbf{'+name+'}',
    for (percent, rate) in rates.iteritems():
        print "&", round(float(rate['OK']) / float(rate['Total']), 2),
    print "\\\\"

# print "Terran:  ", len(matchers['Terran'].training)
# print "Zerg:    ", len(matchers['Zerg'].training)
# print "Protoss: ", len(matchers['Protoss'].training)
