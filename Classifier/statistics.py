import math

def mean(list):
    sum = 0
    for n in list:
        sum += n
    return float(sum) / len(list)


def stddev(list):
    m = mean(list)
    sum = 0
    for n in list:
        sum += math.pow(n - m, 2)
    return math.sqrt(sum / (len(list) - 1))


def unbiased_stddev(list):
    return stddev(list) / c4(float(len(list)))


def c4(N):
    return math.sqrt(
        2.0 / (N-1.0)
    ) * (
        math.gamma(N / 2.0) /
        math.gamma(N / 2.0 - 1.0/2.0)
    )

