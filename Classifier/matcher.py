import math
import statistics

class BuildOrderMatcher:

    training = dict()
    training_sequence = dict()
    training_replay_count = dict()

    distribution = dict()
    # training_sequence = dict()

    def __init__(self):
        self.training = dict()
        self.training_sequence = dict()
        self.distribution = dict()

    def train(self, bos, label):
        for bo in bos:
            if label not in self.training:
                self.training[label] = dict()
                self.training_replay_count[label] = 0
            bo_train = self.training[label]
            if label not in self.training_sequence:
                self.training_sequence[label] = list()
            bo_sequence = self.training_sequence[label]
            bo_repeat = dict()

            for action_dict in bo.actions:
                time = action_dict['time']
                action = action_dict['action']
                supply = action.stats['m_scoreValueFoodUsed'] / 4096

                if action.unit not in bo_repeat:
                    bo_repeat[action.unit] = 0

                if action.unit not in bo_train:
                    bo_train[action.unit] = dict()
                if bo_repeat[action.unit] not in bo_train[action.unit]:
                    bo_train[action.unit][bo_repeat[action.unit]] = []

                bo_train[action.unit][bo_repeat[action.unit]].append(time)
                bo_repeat[action.unit] += 1

                bo_sequence.append(action.unit)

            self.training[label] = bo_train
            self.training_sequence[label] = bo_sequence
            self.training_replay_count[label] += 1

    def build_distribution(self):
        for (label, train) in self.training.iteritems():
            self.distribution[label] = dict()
            for (unit, repeats) in train.iteritems():
                self.distribution[label][unit] = dict()
                for (n, times) in repeats.iteritems():

                    amplitude = float(len(times)) / float(self.training_replay_count[label])
                    # check if at least 50% of the samples have this action
                    # if float(len(times)) / float(self.training_replay_count[label]) <= 0.5:
                        # self.distribution[label][unit][n] = ConstantDistributionFunction(
                        #     p=0.5
                        # )
                        # amplitude = float(len(times)) / float(self.training_replay_count[label])
                        # continue
                    if len(times) < 2:
                        continue

                    mean = statistics.mean(times)
                    sigma = statistics.unbiased_stddev(times)

                    if sigma == 0:
                        continue

                    # if the sigma is larger than 200 it probably is a random sample
                    # and it would help ignoring it
                    # if sigma > 200:
                    #     continue

                    df = NormalDistributionFunction(
                        mean=mean,
                        sigma=sigma,
                        amplitude=amplitude
                    )
                    self.distribution[label][unit][n] = df

                if len(self.distribution[label][unit]) == 0:
                    del self.distribution[label][unit]

    def classify(self, bo):
        results = dict()
        sequencer = dict()
        built=dict()

        for (name, distribution) in self.distribution.iteritems():
            for action_dict in bo.actions:
                if name not in results:
                    results[name] = 1
                    sequencer[name] = dict()
                    built[name] = set()

                time = action_dict['time']
                action = action_dict['action']

                # computes the action sequence numbering, that is, determines
                # if the action is being issued the first, second or nth time.
                if action.unit not in sequencer[name]:
                    sequencer[name][action.unit] = 0
                n = sequencer[name][action.unit]
                sequencer[name][action.unit] += 1

                built[name].add(action.unit)

                if action.unit not in distribution or len(distribution[action.unit]) == 0:
                    # if a unit not in the list is built, apply a decay constant
                    # results[name] *= 0.5
                    continue
                if n not in distribution[action.unit]:
                    # if a unit on the list is built more than the accounted mount,
                    # apply a small decay constant
                    results[name] *= 0.95 / len(distribution[action.unit])
                    continue

                df = distribution[action.unit][n]
                results[name] *= df.apply(time)

                # print name, results[name]
                # print n, action.unit, time, df.apply(time), distribution[action.unit][n]

            # apply a decay for required stuff that was not built
            for (unit, repeats) in distribution.iteritems():
                if unit not in built[name]:
                    # print name, unit, built[name]
                    results[name] *= 0.1 / len(distribution)

        return results


class NormalDistributionFunction:
    def __init__(self, mean, sigma=1.0, amplitude=1.0):
        self.mean = mean
        self.sigma = sigma
        self.amplitude = amplitude

    def apply(self, t):
        if t is None:
            return 0.0
        return self.amplitude * math.exp(-(math.pow(t-self.mean, 2) / (2 * math.pow(self.sigma, 2))))

    def __str__(self):
        return "mean="+str(self.mean) + ", sigma="+str(self.sigma)


class ConstantDistributionFunction:
    p = 1.0

    def __init__(self, p=1.0):
        self.p = p

    def apply(self, t):
        return self.p

    def __str__(self):
        return "p="+str(self.p)
