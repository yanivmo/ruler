import argparse

from line_profiler import LineProfiler

import ruler


class Morning(ruler.Grammar):
    """
    Implementation of the following grammar::

        grammar = who, ' likes to drink ', what;
        who = 'John' | 'Peter' | 'Ann';
        what = tea | juice;
        juice = 'juice';
        tea = 'tea', [' ', milk];
        milk = 'with milk'
    """
    who = ruler.OneOf('John', 'Peter', 'Ann')
    juice = ruler.Rule('juice')
    milk = ruler.Optional(' with milk')
    tea = ruler.Rule('tea', milk)
    what = ruler.OneOf(juice, tea)

    _grammar_ = ruler.Rule(who, ' likes to drink ', what, '\.')


def one_match():
    morning_rule = Morning()
    m, _ = morning_rule.match('Ann likes to drink tea with milk.')
    assert m
    assert m.what.tea.milk


def main():

    def method_name_parser(text):
        parts = text.split('.')
        if len(parts) != 2:
            raise argparse.ArgumentTypeError('Must be of the form class.method but got ' + text)
        for part in parts:
            if not part.isidentifier():
                raise argparse.ArgumentTypeError(part + ' is not a valid identifier')
        return parts

    parser = argparse.ArgumentParser(description="Profile the performance of ruler module")
    parser.add_argument("method_spec", type=method_name_parser, nargs='+',
                        help="The method to profile. Must be formatted as class.method. " +
                             "More than one method can be specified")
    args = parser.parse_args()

    profile = LineProfiler()
    for class_name, method_name in args.method_spec:
        class_type = getattr(ruler.ruler, class_name)
        method = getattr(class_type, method_name)
        profile.add_function(method)
    profile.enable()

    one_match()

    profile.disable()
    profile.print_stats()


if __name__ == '__main__':
    main()
