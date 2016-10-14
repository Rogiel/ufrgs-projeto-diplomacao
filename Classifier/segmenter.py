import imp, os
import parser, build_order, game_data

class Segmenter:
    """
    :type build_order: build_order.BuildOrder
    :param build_order
    """
    def __init__(self, build_order):
        self.unit_count = dict()
        self.build_order = build_order

    def build(self):
        for action in self.build_order.actions:
            unit = action['action'].unit
            if unit not in self.unit_count:
                self.unit_count[unit] = 0
            self.unit_count[unit] += 1

    def find_bulk_of_army(self):
        race = self.build_order.race
        units = {k: v for k, v in self.unit_count.iteritems() if game_data.is_bulk_unit(race, k) and game_data.match_threshold(race, k, v)}
        if len(units) is 0:
            return None
        return max(units, key=lambda i: units[i])

    def find_support_of_army(self):
        race = self.build_order.race
        units = {k: v for k, v in self.unit_count.iteritems() if game_data.is_support_unit(race, k) and game_data.match_threshold(race, k, v)}
        if len(units) is 0:
            return None
        return max(units, key=lambda i: units[i])

    def find_tech(self):
        race = self.build_order.race
        units = {k: v for k, v in self.unit_count.iteritems() if game_data.has_tag(race, k, 'tech') and game_data.match_threshold(race, k, v)}
        if len(units) is 0:
            return None
        return max(units, key=lambda i: units[i])

    def find_upgrade_tech(self):
        race = self.build_order.race
        units = {k: v for k, v in self.unit_count.iteritems() if game_data.has_tag(race, k, 'upgrade-tech')}
        if len(units) is 0:
            return None
        return max(units, key=lambda i: units[i])

    def find_tech_path(self):
        race = self.build_order.race
        units = {k: v for k, v in self.unit_count.iteritems() if game_data.has_tag(race, k, 'tech-path') and game_data.match_threshold(race, k, v)}
        if len(units) is 0:
            return None
        return max(units, key=lambda i: units[i] )


def create_build_name(segmenter):
    bulk = segmenter.find_bulk_of_army()
    support = segmenter.find_support_of_army()
    tech = segmenter.find_tech()
    upgrade_tech = segmenter.find_upgrade_tech()
    tech_path = segmenter.find_tech_path()

    name = []
    if bulk is not None:
        name += [game_data.get_replay_label(segmenter.build_order.race, bulk)]
    if tech_path is not None:
        name += [game_data.get_replay_label(segmenter.build_order.race, tech_path)]
    if support is not None:
        name += [game_data.get_replay_label(segmenter.build_order.race, support)]
    if tech is not None:
        name += [game_data.get_replay_label(segmenter.build_order.race, tech)]
    if upgrade_tech is not None:
        name += [game_data.get_replay_label(segmenter.build_order.race, upgrade_tech)]

    return " ".join(name)


def list_replays(dir):
    for root, directories, files in os.walk(dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            yield filepath

all_builds = {
    "Protoss": {},
    "Zerg": {},
    "Terran": {}
}

replays_dir = os.path.join(os.path.dirname(__file__), 'Replays', 'IEM11')
for replay_file in filter(lambda file: file.endswith('.SC2Replay'), list_replays(replays_dir)):
    # print 'Parsing', replay_file
    # try:
    bos = parser.parse(replay_file)
    for (playerID, bo) in bos.iteritems():
        if len(bo['BuildOrder'].actions) < 20:
            continue
        seg = Segmenter(bo['BuildOrder'])
        race = bo['BuildOrder'].race

        seg.build()
        name = create_build_name(seg)
        if name == "":
            print bo['BuildOrder']
            exit()

        if name not in all_builds[race]:
            all_builds[race][name] = dict()

        all_builds[race][name][replay_file] = playerID
        print name, bo['Name']

    # except:
    #     pass

# print len(all_builds["Protoss"])
print all_builds

# foo = imp.load_source('TrainingSet.index', 'TrainingSet/index.py')
# for (replay_file, playerID) in foo.training_set_replays["Protoss"]["Robo-Glaives"].iteritems():
#     bos = parser.parse(replay_file, truncate=True)
#     player = bos[playerID]
#     bo = player['BuildOrder']
#
#     seg = Segmenter(bo)
#     seg.build()
#     print create_build_name(seg)


# for action in players[1]['BuildOrder'].actions:
#     unit = action['action'].unit
#     if unit == "WarpPrism":
#         print action['time'], action['action'].unit
#         exit()