#!/usr/bin/env python2

import imp

iem10 = 0
iem11 = 0
wcs_spring = 0

foo1 = imp.load_source('TrainingSet.index', 'TrainingSet/index.py')
foo2 = imp.load_source('ValidationSet.index', 'TrainingSet/validation.py')

for d in [foo1.training_set_replays, foo2.validation_set_replays]:
    for (race, builds) in d.iteritems():
        for (name, replay_files) in builds.iteritems():
            for (replay_file, player_id) in replay_files.iteritems():
                if replay_file.startswith("Replays/IEM10"):
                    iem10 += 1
                elif replay_file.startswith("Replays/IEM11"):
                    iem11 += 1
                elif replay_file.startswith('Replays/WCS Spring Championship 2016'):
                    wcs_spring += 1


print iem10, iem11, wcs_spring
print iem10 + iem11 + wcs_spring