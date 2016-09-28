import sys, math

from s2protocol.mpyq import mpyq
from s2protocol import protocol15405
from sklearn.naive_bayes import GaussianNB

import build_order
import game_data
import parser
import utils
import statistics

class BuildOrderMatcher:

    not_build_decay = 0.7
    unexistant_decay = 0.8
    more_units_decay = 0.95

    training = dict()
    training_sequence = dict()

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

    def build_distribution(self):
        for (label, train) in self.training.iteritems():
            self.distribution[label] = dict()
            for (unit, repeats) in train.iteritems():
                self.distribution[label][unit] = dict()
                for (n, times) in repeats.iteritems():
                    if len(times) <= 1:
                        self.distribution[label][unit][n] = ConstantDistributionFunction(
                            p=0.9
                        )
                        continue

                    mean = statistics.mean(times)
                    sigma = statistics.unbiased_stddev(times)

                    print statistics.unbiased_stddev(times), statistics.stddev(times)

                    # if the sigma is larger than 200 it probably is a random sample
                    # and it would help ignoring it
                    # if sigma > 200:
                    #     continue

                    df = NormalDistributionFunction(
                        mean=mean,
                        sigma=sigma * 5
                    )
                    self.distribution[label][unit][n] = df

    def classify(self, bo, ignore_workers=True):
        results = dict()
        n_units = dict()
        for (name, sequence) in self.training_sequence.iteritems():
            if name not in results:
                results[name] = 1.0
                n_units[name] = dict()
            n_unit = n_units[name]

            offset_pointer = 0
            offset_detected = False

            training_dict = self.distribution[name]
            for sequence_unit in sequence:
                if results[name] < 0.0001:
                    break

                if sequence_unit not in n_unit:
                    n_unit[sequence_unit] = 0
                n = n_unit[sequence_unit]
                n_unit[sequence_unit] += 1

                if n not in training_dict[sequence_unit]:
                    continue
                trained_unit = training_dict[sequence_unit][n]
                if offset_detected is False:
                    try:
                        offset_unit = bo.find_nth_action(sequence_unit, n)
                        offset_pointer = offset_unit['time'] - trained_unit.mean
                        offset_detected = True
                    except:
                        results[name] = 0
                        break

                if sequence_unit in game_data.workers and ignore_workers is True\
                        or sequence_unit in game_data.irrelevant_units:
                    continue
                if sequence_unit not in training_dict:
                    # print 'unexistant'
                    results[name] *= self.unexistant_decay
                    continue

                action_dict = bo.find_time_nearest_action(sequence_unit, trained_unit.mean)
                if action_dict is None:
                    # print 'not built', sequence_unit
                    results[name] *= self.not_build_decay
                    continue

                time = action_dict['time'] - offset_pointer
                action = action_dict['action']
                supply = action.stats['m_scoreValueFoodUsed'] / 4096

                try:
                    df = training_dict[action.unit][n]
                    results[name] *= df.apply(time)
                    offset_pointer = time - df.mean
                    # print name, time, df.mean, offset_pointer, df.apply(time), df.apply(time-offset_pointer), results[name]
                except IndexError:
                    results[name] *= self.more_units_decay
                    continue
        return results


    def classify2(self, bo):
        results = dict()
        sequencer = dict()

        for action_dict in bo.actions:
            for (name, distribution) in self.distribution.iteritems():
                if name not in results:
                    results[name] = 1
                    sequencer[name] = dict()

                time = action_dict['time']
                action = action_dict['action']

                # computes the action sequence numbering, that is, determines
                # if the action is being issued the first, second or nth time.
                if action.unit not in sequencer[name]:
                    sequencer[name][action.unit] = 0
                n = sequencer[name][action.unit]

                if action.unit not in distribution:
                    # if a unit not in the list is built, apply a decay constant
                    results[name] *= 0.5
                    continue
                if n not in distribution[action.unit]:
                    # if a unit on the list is built more than the accounted mount,
                    # apply a small decay constant
                    # results[name] *= 0.95
                    continue

                df = distribution[action.unit][n]
                results[name] *= df.apply(time)

                # print name, results[name]
                # print n, time, distribution[action.unit], distribution[action.unit][n]

                sequencer[name][action_dict['action'].unit] += 1
        return results


class NormalDistributionFunction:
    mean = 0.0
    sigma = 1.0

    def __init__(self, mean, sigma=1.0):
        self.mean = mean
        self.sigma = sigma

    def apply(self, t):
        if t is None:
            return 0.0

        return math.exp(-(math.pow(t-self.mean, 2) / (2 * math.pow(self.sigma, 2))))
        # return math.exp(-((t*(t - 2 * self.mean)) / (2 * math.pow(self.sigma, 2))))
        # return math.exp(-(math.pow(t - self.mean, 2))/self.sigma)

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
