from line_profiler import LineProfiler

from ruler import Rule, Optional, OneOf, Grammar


class Morning(Grammar):
    """
    Implementation of the following grammar::

        grammar = who, ' likes to drink ', what;
        who = 'John' | 'Peter' | 'Ann';
        what = tea | juice;
        juice = 'juice';
        tea = 'tea', [' ', milk];
        milk = 'with milk'
    """
    who = OneOf('John', 'Peter', 'Ann')
    juice = Rule('juice')
    milk = Optional(' with milk')
    tea = Rule('tea', milk)
    what = OneOf(juice, tea)

    _grammar_ = Rule(who, ' likes to drink ', what, '\.')


def one_match():
    morning_rule = Morning()
    m, e = morning_rule.match('Ann likes to drink tea with milk.')
    assert m
    assert m.what.tea.milk


if __name__ == '__main__':
    profile = LineProfiler(Rule.match)
    profile.enable()

    one_match()

    profile.disable()
    profile.print_stats()
