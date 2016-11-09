from pytest import raises

import rulre
from rulre import Rule, Optional, OneOf, Grammar


class TestRegexRule:
    def test_whole_match(self):
        r = rulre.RegexRule('abcde')
        m = r.match('abcde')

        assert m.is_matching
        assert m.matching_text == 'abcde'
        assert m.remainder == ''

    def test_partial_match(self):
        r = rulre.RegexRule('abcde')
        m = r.match('abcdefgh')

        assert m.is_matching
        assert m.matching_text == 'abcde'
        assert m.remainder == 'fgh'

    def test_match_not_from_start(self):
        r = rulre.RegexRule('abcde')
        m = r.match('1abcde')

        assert not m.is_matching
        assert m.error_position == 0


class TestRule:
    def test_simplest_rule(self):
        r = Rule.with_name('r1')('a')

        m = r.match('a')
        assert m.is_matching
        assert m.matching_text == 'a'
        assert m.remainder == ''
        assert m.tokens['r1'] == 'a'

        m = r.match('b')
        assert not m.is_matching
        assert m.error_position == 0, m.error_text

    def test_chained_simplest_rules(self):
        r = Rule.with_name('r1')('a', 'b', 'c')

        m = r.match('abcdefg')
        assert m.is_matching
        assert m.matching_text == 'abc'
        assert m.remainder == 'defg'
        assert m.tokens['r1'] == 'abc'

        m = r.match('abdefg')
        assert not m.is_matching
        assert m.error_position == 2, m.error_text

    def test_nested_rules(self):
        r = Rule.with_name('r1')(
                'a',
                Rule.with_name('r1.1')(
                    'b',
                    Rule.with_name('r1.1.1')('c', 'd')),
                Rule.with_name('r1.2')('e'))

        m = r.match('abcde')
        assert m.is_matching
        assert m.matching_text == 'abcde'
        assert m.remainder == ''
        assert m.tokens['r1'] == 'abcde'
        assert m.tokens['r1.1'] == 'bcd'
        assert m.tokens['r1.1.1'] == 'cd'
        assert m.tokens['r1.2'] == 'e'

        m = r.match('abcef')
        assert not m.is_matching
        assert m.error_position == 3, m.error_text


class TestOptionalRule:
    def test_simplest_rule(self):
        r = Optional('a')

        m = r.match('a')
        assert m.is_matching
        assert m.matching_text == 'a'
        assert m.remainder == ''
        assert len(m.tokens) == 0

        m = r.match('b')
        assert m.is_matching
        assert m.matching_text == ''
        assert m.remainder == 'b'
        assert len(m.tokens) == 0

    def test_compound(self):
        r = Rule.with_name('r1')(
                'a',
                Optional.with_name('r1.1')('b'),
                Optional.with_name('r1.2')('c', 'd'),
                'e')

        m = r.match('abcde')
        assert m.is_matching
        assert m.matching_text == 'abcde'
        assert m.remainder == ''
        assert m.tokens['r1'] == 'abcde'
        assert m.tokens['r1.1'] == 'b'
        assert m.tokens['r1.2'] == 'cd'

        m = r.match('acdef')
        assert m.is_matching, m.error_text
        assert m.matching_text == 'acde'
        assert m.remainder == 'f'
        assert m.tokens['r1'] == 'acde'
        assert 'r1.1' not in m.tokens
        assert m.tokens['r1.2'] == 'cd'

        m = r.match('aef')
        assert m.is_matching, m.error_text
        assert m.matching_text == 'ae'
        assert m.remainder == 'f'
        assert m.tokens['r1'] == 'ae'
        assert 'r1.1' not in m.tokens
        assert 'r1.2' not in m.tokens


class TestOneOfRule:
    def test_simplest_rule(self):
        r = OneOf.with_name('letter')('a', 'b', 'c')

        m = r.match('a')
        assert m.is_matching
        assert m.matching_text == 'a'
        assert m.remainder == ''
        assert m.tokens['letter'] == 'a'

        m = r.match('b')
        assert m.is_matching
        assert m.matching_text == 'b'
        assert m.remainder == ''
        assert m.tokens['letter'] == 'b'

        m = r.match('c')
        assert m.is_matching
        assert m.matching_text == 'c'
        assert m.remainder == ''
        assert m.tokens['letter'] == 'c'

        m = r.match('d')
        assert not m.is_matching
        assert m.matching_text == ''
        assert m.remainder == 'd'
        assert len(m.tokens) == 0

    def test_compound(self):
        r = OneOf.with_name('one-of')(
                Rule.with_name('r1')('a'),
                Rule.with_name('r2')('b', '1'),
                Rule.with_name('r3')('b', '2'))

        m = r.match('a')
        assert m.is_matching
        assert m.matching_text == 'a'
        assert m.remainder == ''
        assert m.tokens['r1'] == 'a'
        assert m.tokens['one-of'] == 'a'
        assert 'r2' not in m.tokens
        assert 'r3' not in m.tokens

        m = r.match('b1')
        assert m.is_matching
        assert m.matching_text == 'b1'
        assert m.remainder == ''
        assert m.tokens['r2'] == 'b1'
        assert m.tokens['one-of'] == 'b1'
        assert 'r1' not in m.tokens
        assert 'r3' not in m.tokens

        m = r.match('b3')
        assert not m.is_matching, m.error_text
        assert m.matching_text == 'b'
        assert m.remainder == '3'
        assert m.error_position == 1
        assert 'r1' not in m.tokens
        assert 'r2' not in m.tokens
        assert 'r3' not in m.tokens
        assert 'one-of' not in m.tokens

        m = r.match('b')
        assert not m.is_matching, m.error_text
        assert m.matching_text == 'b'
        assert m.remainder == ''
        assert m.error_position == 1
        assert 'r1' not in m.tokens
        assert 'r2' not in m.tokens
        assert 'r3' not in m.tokens
        assert 'one-of' not in m.tokens


class TestTokenErrors:
    def test_sibling_redefinition(self):
        r = Rule(Rule.with_name('A')('a'),
                 Rule.with_name('A')('b'))

        m = r.match('a')
        assert not m.is_matching, m.error_text
        assert m.matching_text == 'a'
        assert m.error_position == 1
        assert m.tokens['A'] == 'a'

        with raises(rulre.TokenRedefinitionError):
            r.match('ab')

    def test_child_redefinition(self):
        r = Rule.with_name('A')(
                Rule('a',
                     Rule.with_name('A')('b')))

        m = r.match('a')
        assert not m.is_matching, m.error_text
        assert m.matching_text == 'a'
        assert m.error_position == 1

        with raises(rulre.TokenRedefinitionError):
            r.match('ab')

    def test_oneof(self):
        r = OneOf.with_name('A')(
                Rule.with_name('A')('a'),
                Rule.with_name('B')('b'))

        m = r.match('bb')
        assert m.is_matching
        assert m.matching_text == 'b'
        assert m.remainder == 'b'
        assert m.tokens['B'] == 'b'
        assert m.tokens['A'] == 'b'

        with raises(rulre.TokenRedefinitionError):
            r.match('ab')


class TestAutomaticRuleNaming:

    def test_example(self):
        """
        Implementation of the following grammar::

            grammar = who, ' likes to drink ', what;
            who = 'John' | 'Peter' | 'Ann';
            what = tea | juice;
            juice = 'juice';
            tea = 'tea', [ ' with ', milk ];
            milk = 'milk';
        """
        class Morning(Grammar):
            who = OneOf('John', 'Peter', 'Ann')
            juice = Rule('juice')
            milk = Rule('milk')
            tea = Rule('tea', Optional(' with ', milk))
            what = OneOf(juice, tea)

            grammar = Rule(who, ' likes to drink ', what, '\.')

            def __init__(self):
                super(Morning, self).__init__(self.grammar)

        morning_rule = Morning()

        assert morning_rule.grammar.name == 'grammar'
        with raises(rulre.rulre.RuleNamingError):
            morning_rule.grammar.name = ''

        m = morning_rule.match('Ann likes to drink tea with milk.')
        assert m.is_matching
        assert m['who'] == 'Ann'
        assert 'juice' not in m
        assert m.tokens == {
            'grammar': 'Ann likes to drink tea with milk.',
            'who': 'Ann',
            'what': 'tea with milk',
            'milk': 'milk',
            'tea': 'tea with milk'
        }

        m = morning_rule.match('Peter likes to drink tea.')
        assert m.is_matching
        assert m.tokens == {
            'grammar': 'Peter likes to drink tea.',
            'who': 'Peter',
            'what': 'tea',
            'tea': 'tea'
        }

        m = morning_rule.match('Peter likes to drink coffee.')
        assert not m.is_matching
        assert m.error_position == 21

        m = morning_rule.match('Peter likes to drink tea with lemon.')
        assert not m.is_matching
        assert m.error_position == 24


class TestAbstractClasses:
    """Test classes that are not supposed to be used directly."""

    def test_base_rule(self):
        r = rulre.rulre.BaseRule()
        with raises(NotImplementedError):
            r.match('')

    def test_compound_rule(self):
        r = rulre.rulre.CompoundRule('r')
        with raises(NotImplementedError):
            r.match('')
