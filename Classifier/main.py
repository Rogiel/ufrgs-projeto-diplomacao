import parser
import pickle
import mysql.connector
import build_order
import matcher
import os
import imp
import utils
import matplotlib.pyplot as pyplot
import pprint

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

        replay_files_iter = replay_files.iteritems()
        next(replay_files_iter)
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

rates = dict()
for (race, builds) in foo.training_set_replays.iteritems():
    for (name, replay_files) in builds.iteritems():
        if name not in rates:
            rates[name] = {
                'Total': 0,
                'OK': 0
            }

        for (replay_file, pid) in replay_files.iteritems():
            bos = parser.parse(replay_file, truncate=True)
            for (playerID, bo) in bos.iteritems():
                if playerID != pid:
                    continue
                results = matchers[bo['Race']].classify(bo['BuildOrder'])
                probable = utils.get_most_probable_build(results)[0]

                rates[name]['Total'] += 1
                if probable == name:
                    rates[name]['OK'] += 1

                print name, "->", probable

for (name, rate) in rates.iteritems():
    print name, float(rate['OK']) / float(rate['Total']), "(" + str(rate['OK']) + "/" + str(rate['Total']) + ")"

# print "Terran:  ", len(matchers['Terran'].training)
# print "Zerg:    ", len(matchers['Zerg'].training)
# print "Protoss: ", len(matchers['Protoss'].training)
