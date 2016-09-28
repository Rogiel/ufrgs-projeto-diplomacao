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

force_train = False
trained_set_file = os.path.join(os.path.dirname(__file__), 'trained.raw')

# if not os.path.exists(trained_set_file) or force_train:
#     cnx = mysql.connector.connect(user='root', password='1020rr',
#                                   host='127.0.0.1',
#                                   database='sc2')
#
#     cnx2 = mysql.connector.connect(user='root', password='1020rr',
#                                   host='127.0.0.1',
#                                   database='sc2')
#     cursor = cnx.cursor()
#     cursor.execute('SELECT bo.id, t.name, r.game_race_identifier FROM build_order AS bo '
#                    'LEFT JOIN build_order_translation AS t ON(t.translatable_id = bo.id AND t.locale = "en")'
#                    'LEFT JOIN race                    AS r ON(r.id = bo.race_id)'
#                    'WHERE t.name IS NOT NULL')
#
#     trainingSet = {
#         'Terran':  list(),
#         'Zerg':    list(),
#         'Protoss': list()
#     }
#     for (bid, name, race) in cursor:
#         bo = build_order.BuildOrder(
#             race=race,
#             name=name
#         )
#
#         invalid = True
#
#         bo_cursor = cnx2.cursor(buffered=True)
#         bo_cursor.execute(
#             'SELECT a.id, u1.identifier, u2.game_identifier, a.game_time, a.supply_used FROM build_order_action AS a '
#             'LEFT JOIN unit    AS u1 ON(u1.id = a.unit_id)'
#             'LEFT JOIN upgrade AS u2 ON(u2.id = a.upgrade_id)'
#             'WHERE a.build_order_id = '+str(bid)+' '
#             'ORDER BY sequence ASC'
#         )
#
#         timeOffsetSet = False
#         timeOffset = 0
#         for (aid, uid, upid, time, supply) in bo_cursor:
#             if time is None:
#                 invalid = True
#                 break
#             # if timeOffsetSet is False:
#             #     timeOffset = time
#             #     timeOffsetSet = True
#
#             invalid = False
#
#             id = uid if uid is not None else upid
#
#             bo.add_action(time - timeOffset, build_order.BuildUnitAction(
#                 unit=id,
#                 stats={
#                     'm_scoreValueFoodUsed': supply * 4096
#                 }
#             ))
#
#         if bo.name in ['build1', 'Zerg opening', '1 Gate Expand into Oracle Opening (Patience)', 'Trip-Hatch Roaches',
#                        'Standard Hatch First Opening (HyuN)', 'ZvT', 'Standard Reaper Expand Opening (Reality)',
#                        'Fenner\'s Extractors Bandit', '1 Rax Expand (Semper)']:
#             continue
#         # if 'opening' in bo.name.lower():
#         #     continue
#
#         # print bo
#
#         if not invalid:
#             trainingSet[race].append(bo)
#
#     matchers = {
#         'Terran':  matcher.BuildOrderMatcher(),
#         'Zerg':    matcher.BuildOrderMatcher(),
#         'Protoss': matcher.BuildOrderMatcher()
#     }
#
#     for (race, matcher) in matchers.iteritems():
#         matchers[race].train(trainingSet[race])
#
#     f = file(trained_set_file, 'w')
#     pickle.dump(matchers, f)
#     f.close()

# matchers = pickle.load(file(trained_set_file))

matchers = {
    'Terran':  matcher.BuildOrderMatcher(),
    'Zerg':    matcher.BuildOrderMatcher(),
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
        for (replay_file, playerID) in replay_files.iteritems():
            bos = parser.parse(replay_file, truncate=True)
            player = bos[playerID]
            bo = player['BuildOrder']

            print replay_file, player['Name']

            if player['Race'] != race:
                print 'Invalid race for replay '+replay_file+'. Given '+player['Race']+', expected '+race
                exit()
            bo.name = name
            matchers[race].train([bo], name)

for matcher in matchers.itervalues():
    matcher.build_distribution()

# for race, matcher in matchers.iteritems():
#     for bo_name in matcher.distribution.iterkeys():
#         for unit_name in matcher.distribution[bo_name].iterkeys():
#             lengends = list()
#             for unit, actions in matcher.distribution[bo_name].iteritems():
#                 for (n, action) in actions.iteritems():
#                     t = list()
#                     s = list()
#                     i = 0
#
#                     if unit != unit_name:
#                         continue
#
#                     print action
#                     lengends.append(unit_name+" #"+str(n))
#                     for x in range(0, 1200*10, 1):
#                         s.append(0.0)
#                         t.append(x)
#
#                         s[i] += action.apply(x/10.0)
#                         i += 1
#                     pyplot.plot(t, s)
#             pyplot.legend(lengends)
#
#             dir = os.path.join('Graphs', race, bo_name)
#             if not os.path.exists(os.path.dirname(dir)):
#                 os.mkdir(os.path.dirname(dir))
#             if not os.path.exists(dir):
#                 os.mkdir(dir)
#             pyplot.savefig(os.path.join(dir, unit_name+'.png'))
#             pyplot.close()
# exit()

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
                results = matchers[bo['Race']].classify2(bo['BuildOrder'])
                probable = utils.get_most_probable_build(results)[0]

                rates[name]['Total'] += 1
                if probable == name:
                    rates[name]['OK'] += 1

                print name, "->", probable, results

for (name, rate) in rates.iteritems():
    print name, float(rate['OK'])/float(rate['Total'])

# print "Terran:  ", len(matchers['Terran'].training)
# print "Zerg:    ", len(matchers['Zerg'].training)
# print "Protoss: ", len(matchers['Protoss'].training)
