
class BuildOrder:
    race = None
    actions = list()
    name = None

    def __init__(self, race, name=None):
        self.race = race
        self.actions = list()
        self.name = name

    def add_action(self, time, action):
        self.actions.append({
            'time': time,
            'action': action
        })

    def __str__(self):
        output = 'Race: {RaceName}\n'.format(**{
            'RaceName': self.race
        })
        for action in self.actions:
            output += ' {Time}: {Action}'.format(**{
                'Time': action['time'],
                'Action': action['action']
            })+'\n'

        return output

    def find_nth_action(self, unit, n):
        try:
            return filter(lambda x: x['action'].unit == unit, self.actions)[n]
        except IndexError:
            return None

    def find_time_nearest_action(self, unit, t):
        diff = ''
        nearest_action = None
        for action in filter(lambda x: x['action'].unit == unit, self.actions):
            if abs(t - action['time']) < diff:
                diff = abs(t - action['time'])
                nearest_action = action
        return nearest_action

    def find_supply_nearest_action(self, unit, s):
        diff = ''
        nearest_action = None
        for action in filter(lambda x: x['action'].unit == unit, self.actions):
            if abs(s - action['action'].stats['m_scoreValueFoodUsed'] / 4096) < diff:
                diff = abs(s - action['action'].stats['m_scoreValueFoodUsed'] / 4096)
                nearest_action = action
        return nearest_action

    def build_feature_vector(self, races):
        race = races[self.race]
        feature_vector = []
        for action in self.actions:
            if action['action'].unit not in race:
                continue
            unit_data = race[action['action'].unit]

            action_vector = list()
            for i in range(len(race)):
                action_vector.insert(i, 0)
            action_vector[unit_data['id']] = 1

            feature_vector.append(action_vector)

        return feature_vector

class BuildUnitAction:

    stats = None
    unit = None

    def __init__(self, stats, unit):
        self.stats = stats
        self.unit = unit

    def __str__(self):
        return '{Supply} {UnitID}'.format(**{
            'Supply': self.stats['m_scoreValueFoodUsed']/4096,
            'UnitID': self.unit
        })
