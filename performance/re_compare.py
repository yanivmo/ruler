"""
This module compares Ruler performance to that of the Python standard
re library. The idea is to match the same few lines of text and
compare how long it takes using re and ruler.

Since the measurements always have non-deterministic, but always
positive, measurement errors, we will make many short measurements
and compare the fastest ones encountered.
"""

import re
import timeit

import ruler as r

TIMEIT_ITERATIONS = 10000
ATTEMPTS_COUNT = 50

# These are the strings that will be matched
ann_likes_juice = 'Ann likes to drink juice'
peter_likes_tea = 'Peter likes to drink tea'
john_likes_tea_with_milk = 'John likes to drink tea with milk'


class ReTimer(object):
    """
    Match and time the strings using the Python standard re library
    """

    def __init__(self):
        self.grammar = re.compile(r"""
            (?P<who> John|Peter|Ann )
            [ ]likes[ ]to[ ]drink
            [ ](?P<what>
                    (?P<juice> juice )
                    |
                    (?P<tea> tea ([ ]with[ ](?P<milk> milk ))?)
              )""", re.VERBOSE)

        self.timer = timeit.Timer('self.match()', globals=locals())

    def match(self):
        g = self.grammar.match(ann_likes_juice).groupdict()
        assert g['who'] == 'Ann'
        assert g['what'] == 'juice'
        assert g['juice'] is not None
        assert g['tea'] is None
        assert g['milk'] is None
        g = self.grammar.match(peter_likes_tea).groupdict()
        assert g['who'] == 'Peter'
        assert g['what'] == 'tea'
        assert g['juice'] is None
        assert g['tea'] is not None
        assert g['milk'] is None
        g = self.grammar.match(john_likes_tea_with_milk).groupdict()
        assert g['who'] == 'John'
        assert g['what'] == 'tea with milk'
        assert g['juice'] is None
        assert g['tea'] is not None
        assert g['milk'] is not None

    def time(self):
        return self.timer.timeit(TIMEIT_ITERATIONS)


class RulerTimer(object):
    """
    Match and time the strings using Ruler library
    """

    def __init__(self):
        class MorningDrink(r.Grammar):
            who = r.OneOf('John', 'Peter', 'Ann')
            juice = r.Rule('juice')
            milk = r.Rule('milk')
            tea = r.Rule('tea', r.Optional(' with ', milk))
            what = r.OneOf(juice, tea)

            _grammar_ = r.Rule(who, ' likes to drink ', what)

        self.grammar = MorningDrink()

        self.timer = timeit.Timer('self.match()', globals=locals())

    def match(self):
        m, e = self.grammar.match(ann_likes_juice)
        assert m.who == 'Ann'
        assert m.what == 'juice'
        assert m.what.juice
        assert not m.what.tea
        # assert not m.what.tea.milk
        m, e = self.grammar.match(peter_likes_tea)
        assert m.who == 'Peter'
        assert m.what == 'tea'
        assert not m.what.juice
        assert m.what.tea
        # assert not m.what.tea.milk
        m, e = self.grammar.match(john_likes_tea_with_milk)
        assert m.who == 'John'
        assert m.what == 'tea with milk'
        assert not m.what.juice
        assert m.what.tea
        assert m.what.tea.milk

    def time(self):
        return self.timer.timeit(TIMEIT_ITERATIONS)


def main():
    re_timer = ReTimer()
    ruler_timer = RulerTimer()

    re_measurements = []
    ruler_measurements = []

    for attempt in range(ATTEMPTS_COUNT):
        print('Attempt {} out of {}...'.format(attempt+1, ATTEMPTS_COUNT))
        re_measurements.append(re_timer.time())
        ruler_measurements.append(ruler_timer.time())
        print('    re:    {:.3f} {}'.format(re_measurements[-1],
                                            'New record!' if re_measurements[-1] == min(re_measurements) else ''))
        print('    ruler: {:.3f} {}'.format(ruler_measurements[-1],
                                            'New record!' if ruler_measurements[-1] == min(ruler_measurements) else ''))
    print('Performance ratio: {}'.format(int(min(ruler_measurements) / min(re_measurements))))


if __name__ == '__main__':
    main()
