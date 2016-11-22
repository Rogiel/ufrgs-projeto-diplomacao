import tabulate
import numpy
import pandas

test = {
    'BO1': {
        'BO1': 100,
        'BO2': 100,
        'BO3': 100
    },
    'BO2': {
        'BO1': 100,
        'BO2': 100,
        'BO3': 100
    },
    'BO3': {
        'BO1': 100,
        'BO2': 100,
        'BO3': 100
    }
}

dataframe = pandas.DataFrame()
dataframe.set_value('test1', 'test2', 100)
dataframe.set_value('test1', 'test2', 100)
dataframe.set_value('test2', 'test1', 100)
dataframe.set_value('test2', 'test1', 100)
dataframe = dataframe.sort_index(axis=0)
dataframe = dataframe.sort_index(axis=1)

print dataframe.to_latex()
