from pytest import raises

import rulre
from rulre import Rule, Optional, OneOf, Grammar


class TestRegexRule:
    def test_whole_match(self):
        r = rulre.RegexRule('abcde')
        m, e = r.match('abcde')

        assert m
        assert not e
        assert str(m) == 'abcde'

    def test_partial_match(self):
        r = rulre.RegexRule('abcde')
        m, e = r.match('abcdefgh')

        assert m
        assert not e
        assert str(m) == 'abcde'

    def test_match_not_from_start(self):
        r = rulre.RegexRule('abcde')
        m, e = r.match('1abcde')

        assert not m
        assert e
        assert e.position == 0


class TestRule:
    def test_simplest_rule(self):
        r = Rule.with_name('r1')('a')
        assert r.name == 'r1'

        m, e = r.match('a')
        assert m and not e
        assert str(m) == 'a'

        m, e = r.match('b')
        assert e and not m
        assert e.position == 0, e.description

    def test_chained_simplest_rules(self):
        r = Rule('a', 'b', 'c')

        m, e = r.match('abcdefg')
        assert m and not e
        assert str(m) == 'abc'

        m, e = r.match('abdefg')
        assert e and not m
        assert e.position == 2, e.description

    def test_nested_rules(self):
        class G(Grammar):
            cd = Rule('c', 'd')
            bcd = Rule('b', cd)
            e = Rule('e')
            abcd = Rule('a', bcd, e)

            def __init__(self):
                super(G, self).__init__(self.abcd)

        g = G()

        m, e = g.match('abcde')
        assert m and not e
        assert str(m) == 'abcde'
        assert str(m.bcd) == 'bcd'
        assert str(m.bcd.cd) == 'cd'
        assert str(m.e) == 'e'

        m, e = g.match('abcef')
        assert e and not m
        assert e.position == 3, e.description


class TestOptionalRule:
    def test_simplest_rule(self):
        r = Optional('a')

        m, e = r.match('a')
        assert m and not e
        assert str(m) == 'a'

        m, e = r.match('b')
        assert m and not e
        assert str(m) == ''

    def test_optional_child(self):
        r = Rule('a',
                 Optional.with_name('r1')('b'),
                 Optional.with_name('r2')('c', 'd'),
                 'e')

        m, e = r.match('abcde')
        assert m and not e
        assert str(m) == 'abcde'
        assert str(m.r1) == 'b'
        assert str(m.r2) == 'cd'

        m, e = r.match('acdef')
        assert m and not e
        assert str(m) == 'acde'
        assert str(m.r1) == ''
        assert str(m.r2) == 'cd'

        m, e = r.match('aef')
        assert m and not e
        assert str(m) == 'ae'
        assert str(m.r1) == ''
        assert str(m.r2) == ''


class TestOneOfRule:
    def test_simplest_rule(self):
        r = OneOf('a', 'b', 'c')

        m, e = r.match('a')
        assert m and not e
        assert str(m) == 'a'

        m, e = r.match('b')
        assert m and not e
        assert str(m) == 'b'

        m, e = r.match('c')
        assert m and not e
        assert str(m) == 'c'

        m, e = r.match('d')
        assert e and not m
        assert e.position == 0, e.description

    def test_compound(self):
        r = OneOf(Rule.with_name('r1')('a'),
                  Rule.with_name('r2')('b', '1'),
                  Rule.with_name('r3')('b', '2'))

        m, e = r.match('a')
        assert m and not e
        assert str(m) == 'a'
        assert str(m.r1) == 'a'
        assert not m.r2
        assert not m.r3

        m, e = r.match('b1')
        assert m and not e
        assert str(m) == 'b1'
        assert str(m.r2) == 'b1'
        assert not m.r1
        assert not m.r3

        m, e = r.match('b3')
        assert e and not m
        assert e.position == 1

        m, e = r.match('b')
        assert e and not m
        assert e.position == 1

    def test_flattening(self):
        r = OneOf(
            'a',
            'b',
            Rule(
                'c',
                Rule.with_name('d')('d')
            ))

        m, e = r.match('a')
        assert m and not e
        assert str(m) == 'a'

        m, e = r.match('b')
        assert m and not e
        assert str(m) == 'b'
        with raises(AttributeError):
            assert str(m.d) == ''

        m, e = r.match('cd')
        assert m and not e
        assert str(m) == 'cd'
        assert str(m.d) == 'd'


class TestTokenErrors:
    def test_sibling_redefinition(self):
        r = Rule(Rule.with_name('A')('a'),
                 Rule.with_name('A')('b'))

        m, e = r.match('a')
        assert e and not m
        assert e.position == 1

        with raises(rulre.TokenRedefinitionError):
            r.match('ab')

    def test_child_redefinition(self):
        r = Rule.with_name('x')('a',
                                Rule.with_name('x')('b',
                                                    Rule.with_name('x')('c')))

        m, e = r.match('a')
        assert e and not m
        assert e.position == 1

        m, e = r.match('abc')
        assert m and not e
        assert str(m) == 'abc'
        assert str(m.x) == 'bc'
        assert str(m.x.x) == 'c'

    def test_oneof(self):
        r = OneOf(Rule.with_name('A')('a'),
                  Rule.with_name('A')('b'))

        with raises(rulre.TokenRedefinitionError):
            r.match('ab')

    def test_flattened(self):
        r = Rule(
            Rule.with_name('xx')('a'),
            Rule(
                Rule.with_name('yy')('b'),
                Optional(
                    Rule.with_name('xx')('c'))
            )
        )

        m, e = r.match('ab!')
        assert m and not e
        assert str(m) == 'ab'
        assert str(m.xx) == 'a'
        assert str(m.yy) == 'b'

        with raises(rulre.TokenRedefinitionError):
            r.match('abc')


class TestAutomaticRuleNaming:
    def test_example(self):
        """
        Implementation of the following grammar::

            grammar = who, ' likes to drink ', what;
            who = 'John' | 'Peter' | 'Ann';
            what = tea | juice;
            juice = 'juice';
            tea = 'tea', [' ', with_milk];
            with_milk = 'with milk'
        """

        class Morning(Grammar):
            who = OneOf('John', 'Peter', 'Ann')
            juice = Rule('juice')
            maybe_milk = Optional(' with milk')
            tea = Rule('tea', maybe_milk)
            what = OneOf(juice, tea)

            grammar = Rule(who, ' likes to drink ', what, '\.')

            def __init__(self):
                super(Morning, self).__init__(self.grammar)

        morning_rule = Morning()

        assert morning_rule.grammar.name == 'grammar'
        with raises(rulre.rulre.RuleNamingError):
            morning_rule.grammar.name = ''

        m, e = morning_rule.match('Ann likes to drink tea with milk.')
        assert m
        assert str(m.who) == 'Ann'
        assert str(m.what) == 'tea with milk'
        assert not m.what.juice
        assert m.what.tea
        assert str(m.what.tea.maybe_milk) != ''

        m, e = morning_rule.match('Peter likes to drink tea.')
        assert m
        assert str(m.who) == 'Peter'
        assert str(m.what) == 'tea'
        assert not m.what.juice
        assert m.what.tea
        assert str(m.what.tea.maybe_milk) == ''

        m, e = morning_rule.match('Peter likes to drink coffee.')
        assert e and not m
        assert e.position == 21

        m, e = morning_rule.match('Peter likes to drink tea with lemon.')
        assert e and not m
        assert e.position == 24


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
