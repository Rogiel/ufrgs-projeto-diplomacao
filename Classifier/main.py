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
rates = dict()
classification_thresholds = dict()

validationSet = imp.load_source('ValidationSet.index', 'TrainingSet/validation.py')
for (race, builds) in validationSet.validation_set_replays.iteritems():
    for (name, replay_files) in builds.iteritems():
        if name not in rates:
            rates[name] = {
                'Total': 0,
                'OK': 0
            }

        # skip = int(len(replay_files) * 0.2)
        # n = 0

        for (replay_file, pid) in replay_files.iteritems():
            bos = parser.parse(replay_file, truncate=True)
            for (playerID, bo) in bos.iteritems():
                if playerID != pid:
                    continue
                results = matchers[bo['Race']].classify(bo['BuildOrder'])
                (probable, p) = utils.get_most_probable_build(results)

                if probable not in classification_thresholds or classification_thresholds[probable] > p:
                    classification_thresholds[probable] = p

                rates[name]['Total'] += 1
                if probable == name:
                    rates[name]['OK'] += 1

                print name, "->", probable, p

for (name, rate) in rates.iteritems():
    print name, float(rate['OK']) / float(rate['Total']), "(" + str(rate['OK']) + "/" + str(rate['Total']) + ")"

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
    print '\\textbf{' + name + '}',
    for (percent, rate) in rates.iteritems():
        print "&", round(float(rate['OK']) / float(rate['Total']), 2),
    print "\\\\"

print
print ' == WON TEST =='
print

won_rates = dict()

for replay_file in list_replays('Replays'):
    try:
        bos = parser.parse(replay_file, truncate=True, lastedTime=True)
        classified = 0
        for (playerID, bo) in bos.iteritems():
            if bo['Race'] != 'Protoss':
                continue

            results = matchers[bo['Race']].classify(bo['BuildOrder'])
            (probable, p) = utils.get_most_probable_build(results)

            if p < classification_thresholds[probable]:
                continue

            bo['Classified'] = probable
            classified += 1

        if classified == 2:
            bo1 = bos[1]['Classified']
            bo2 = bos[2]['Classified']

            if bo1 not in won_rates:
                won_rates[bo1] = dict()
            if bo2 not in won_rates[bo1]:
                won_rates[bo1][bo2] = {
                    'Total': 0,
                    'Won': 0,
                    'Survive': 0
                }

            if bo2 not in won_rates:
                won_rates[bo2] = dict()
            if bo1 not in won_rates[bo2]:
                won_rates[bo2][bo1] = {
                    'Total': 0,
                    'Won': 0,
                    'Survive': 0
                }

            won_rates[bo1][bo2]['Total'] += 1
            won_rates[bo2][bo1]['Total'] += 1

            if bos[1]['Win']:
                won_rates[bo1][bo2]['Won'] += 1
            if bos[2]['Win']:
                won_rates[bo2][bo1]['Won'] += 1

            if bos[1]['SurvivedUntil'] > 10 * 60:
                won_rates[bo1][bo2]['Survive'] += 1
            if bos[2]['SurvivedUntil'] > 10 * 60:
                won_rates[bo2][bo1]['Survive'] += 1
    except:
        continue

print won_rates

import pandas

pandas.options.display.float_format = '{:.2f}'.format

dataframe = pandas.DataFrame()
for (bo1, level1) in won_rates.iteritems():
    for (bo2, rate) in level1.iteritems():
        # print bo1, bo2, float(rate['Won']) / float(rate['Total']), "(" + str(rate['Won']) + "/" + str(
        #     rate['Total']) + ")"
        dataframe.set_value(bo1, bo2, float(rate['Won']) / float(rate['Total']))
dataframe = dataframe.sort_index(axis=0)
dataframe = dataframe.sort_index(axis=1)
print dataframe.to_latex(na_rep='-', bold_rows=True)

with open('../Report/Tables/Win-rate.tex', 'wb') as f:
    f.write(dataframe.to_latex(na_rep='-', bold_rows=True))

print
print ' == NOT LOSE UNTIL 10 MIN =='
print

dataframe = pandas.DataFrame()
for (bo1, level1) in won_rates.iteritems():
    for (bo2, rate) in level1.iteritems():
        # print bo1, bo2, float(rate['Survive']) / float(rate['Total']), "(" + str(rate['Survive']) + "/" + str(
        #     rate['Total']) + ")"
        dataframe.set_value(bo1, bo2, float(rate['Survive']) / float(rate['Total']))
dataframe = dataframe.sort_index(axis=0)
dataframe = dataframe.sort_index(axis=1)
print dataframe.to_latex(na_rep='-', bold_rows=True)


with open('../Report/Tables/Survival-rate.tex', 'wb') as f:
    f.write(dataframe.to_latex(na_rep='-', bold_rows=True))