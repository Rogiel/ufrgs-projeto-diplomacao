import parser
import matcher
import os
import utils
import copy
import pprint
import shutil
import pickle

groups_file = os.path.join(os.path.dirname(__file__), 'groups.raw')

matchers = {
    'Terran':  matcher.BuildOrderMatcher(),
    'Zerg':    matcher.BuildOrderMatcher(),
    'Protoss': matcher.BuildOrderMatcher()
}
replays_dir = os.path.join(os.path.dirname(__file__), 'Replays', 'IEM11')

def list_replays(dir):
    for root, directories, files in os.walk(dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            yield filepath

for replay_file in filter(lambda file: file.endswith('.SC2Replay'), list_replays(replays_dir)):
    print 'Parsing', replay_file
    try:
        bos = parser.parse(replay_file)
        for (playerID, bo) in bos.iteritems():
            if len(bo['BuildOrder'].actions) < 20:
                continue
            bo['BuildOrder'].name = replay_file + '#'+bo['Name']
            matchers[bo['Race']].train([bo['BuildOrder']], label=bo['BuildOrder'].name)
            print len(bo['BuildOrder'].actions), bo['BuildOrder'].name
    except:
        pass

print "Terran:  ", len(matchers['Terran'].training)
print "Zerg:    ", len(matchers['Zerg'].training)
print "Protoss: ", len(matchers['Protoss'].training)

matchers['Terran'].build_distribution()
matchers['Zerg'].build_distribution()
matchers['Protoss'].build_distribution()

groups = {
    'Terran':  dict(),
    'Zerg':    dict(),
    'Protoss': dict(),
}
translation_table = {
    'Terran':  dict(),
    'Zerg':    dict(),
    'Protoss': dict(),
}

for replay_file in filter(lambda file: file.endswith('.SC2Replay'), list_replays(replays_dir)):
    try:
        players = parser.parse(replay_file, truncate=False)
        print replay_file
        for (playerID, player) in players.iteritems():
            bo = player['BuildOrder']
            race = player['Race']
            matcher = copy.deepcopy(matchers[race])
            name = replay_file + '#'+player['Name']

            if len(bo.actions) < 20:
                continue

            if name in matcher.training:
                del matcher.training[name]
                del matcher.training_sequence[name]

            results = utils.sort_by_probability(matcher.classify(bo))

            # print results
            probable = utils.get_most_probable_build(results)
            probability = probable[1]
            if probability is None:
                probability = 0.0

            group = None
            if name in translation_table[race]:
                group = groups[race][translation_table[race][probable[0]]]
            else:
                if probability >= 0.8:
                    if probable[0] not in groups[race]:
                        group = groups[race][probable[0]] = list()
                        translation_table[race][name] = probable[0]
                    else:
                        group = groups[race][probable[0]]
                    group.append(name)
                else:
                    group = groups[race][name] = list()
            group.append(name)
            print '%-20s %-40s (%s %%)' % (player['Name'], probable[0], probability * 100)
    except:
        pass
    print

f = file(groups_file, 'w')
pickle.dump(groups, f)
f.close()

groups = pickle.load(file(groups_file))

group_index = {
    'Zerg': 1,
    'Terran': 1,
    'Protoss': 1
}

def copy_replay(replay, folder, identifier):
    splitted = replay.split('#', 2)

    final_name = os.path.basename(splitted[0])[:-10] + ' - ' + splitted[1] + '.SC2Replay'
    final_name = final_name.replace('<sp/>', '', 100)
    final_name = final_name.replace('<', '', 100)
    final_name = final_name.replace('>', '', 100)

    shutil.copyfile(splitted[0], os.path.join(folder, final_name))

    identifier.write(final_name)
    identifier.write(':')
    identifier.write(base)
    identifier.write('\r\n')

for (race, race_groups) in groups.iteritems():
    for (base, replays) in race_groups.iteritems():
        if base is None:
            continue

        path = os.path.join('Classified', race, 'Build '+str(group_index[race]))
        try:
            os.mkdir(path)
        except:
            pass
        splitted = base.split('#', 2)

        final_name = os.path.basename(splitted[0])[:-10]+' - '+splitted[1]+'.SC2Replay'
        final_name = final_name.replace('<sp/>', '', 100)
        final_name = final_name.replace('<', '', 100)
        final_name = final_name.replace('>', '', 100)

        identifier = file(os.path.join(path, 'reference.txt'), 'w')
        copy_replay(base, path, identifier)
        # shutil.copyfile(base, os.path.join(path, os.path.basename(base[0])))
        for replay_file in replays:
            copy_replay(replay_file, path, identifier)

        group_index[race] += 1
        identifier.close()

pprint.pprint(groups)
