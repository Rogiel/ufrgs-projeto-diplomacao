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

max_time = 8 * 60

for race, matcher in matchers.iteritems():
    for bo_name in matcher.distribution.iterkeys():
        for unit_name in matcher.distribution[bo_name].iterkeys():
            lengends = list()
            for unit, actions in matcher.distribution[bo_name].iteritems():
                for (n, action) in actions.iteritems():
                    t = list()
                    s = list()
                    i = 0

                    if unit != unit_name:
                        continue

                    print action
                    lengends.append(unit_name+" #"+str(n))
                    for x in range(0, max_time*10, 1):
                        s.append(0.0)
                        t.append(x)

                        s[i] += action.apply(x/10.0)
                        i += 1
                    pyplot.plot(t, s)
            pyplot.legend(lengends)

            dir = os.path.join('Graphs', race, bo_name)
            if not os.path.exists(os.path.dirname(dir)):
                os.mkdir(os.path.dirname(dir))
            if not os.path.exists(dir):
                os.mkdir(dir)
            pyplot.savefig(os.path.join(dir, unit_name+'.png'), transparent=True)
            pyplot.close()

