from pytest import raises

from ruler import Rule, Optional, OneOf, Grammar, RegexRule
from ruler.base_rules import BaseRule, BaseCompoundRule, RuleNamingError
from ruler.rules import CompoundRule


class TestRegexRule:
    def test_whole_match(self):
        r = RegexRule('abcde')
        assert r.match('abcde')
        assert r.matched == 'abcde'

    def test_partial_match(self):
        r = RegexRule('abcde')
        assert r.match('abcdefgh')
        assert r.matched == 'abcde'

    def test_match_not_from_start(self):
        r = RegexRule('abcde')
        assert not r.match('1abcde')
        assert r.error.position == 0


class TestRule:
    def test_simplest_rule(self):
        r = Rule.with_name('r1')('a')
        assert r.name == 'r1'

        assert r.match('a')
        assert r.matched == 'a'

        assert not r.match('b')
        assert r.error.position == 0, r.error.description

    def test_actual_regex(self):
        r = Rule('A number: ', '\d+', ' \[(x\w*x)\]')
        assert r.match('A number: 12345 [xx]')
        assert r.matched == 'A number: 12345 [xx]'

    def test_chained_simplest_rules(self):
        r = Rule('a', 'b', 'c')

        assert r.match('abcdefg')
        assert r.matched == 'abc'

        assert not r.match('abdefg')
        assert r.error.position == 2

    def test_nested_rules(self):
        class G(Grammar):
            cd = Rule('c', 'd')
            bcd = Rule('b', cd)
            e = Rule('e')
            grammar = Rule('a', bcd, e)

        g = G.create()

        assert g.match('abcde')
        assert g.matched == 'abcde'
        assert g.bcd.matched == 'bcd'
        assert g.bcd.cd.matched == 'cd'
        assert g.e.matched == 'e'

        assert not g.match('abcef')
        assert g.error.position == 3, g.error.description

    def test_rule_reuse(self):
        class G(Grammar):
            reused = Rule('..')
            a = Rule('a', reused)
            b = Rule('b', reused)
            c = Rule('c', reused)
            grammar = Rule(a, b, c)

        g = G.create()
        assert g.match('a11b22c33')
        assert g.a.matched == 'a11'
        assert g.a.reused.matched == '11'
        assert g.b.matched == 'b22'
        assert g.b.reused.matched == '22'
        assert g.c.matched == 'c33'
        assert g.c.reused.matched == '33'


class TestOptionalRule:
    def test_simplest_rule(self):
        r = Optional('a')

        assert r.match('a')
        assert r.matched == 'a'

        assert r.match('b')
        assert r.matched is None

    def test_optional_child(self):
        r = Rule('a',
                 Optional.with_name('r1')('b'),
                 Optional.with_name('r2')('c', 'd'),
                 'e')

        assert r.match('abcde')
        assert r.matched == 'abcde'
        assert r.r1.matched == 'b'
        assert r.r2.matched == 'cd'

        assert r.match('acdef')
        assert r.matched == 'acde'
        assert r.r1.matched is None
        assert r.r2.matched == 'cd'

        assert r.match('aef')
        assert r.matched == 'ae'
        assert r.r1.matched is None
        assert r.r2.matched is None


class TestOneOfRule:
    def test_simplest_rule(self):
        r = OneOf('a', 'b', 'c')

        assert r.match('a')
        assert r.matched == 'a'

        assert r.match('b')
        assert r.matched == 'b'

        assert r.match('c')
        assert r.matched == 'c'

        assert not r.match('d')
        assert r.error.position == 0, r.error.description

    def test_compound(self):
        r = OneOf(Rule.with_name('r1')('a'),
                  Rule.with_name('r2')('b', '1'),
                  Rule.with_name('r3')('b', '2'))

        assert r.match('a')
        assert r.matched == 'a'
        assert r.r1.matched == 'a'
        assert r.r2.matched is None
        assert r.r3.matched is None

        assert r.match('b1')
        assert r.matched == 'b1'
        assert r.r2.matched == 'b1'
        assert r.r1.matched is None
        assert r.r3.matched is None

        assert not r.match('b3')
        assert r.error.position == 1
        expected = ('Mismatch at 1:\n  b3\n   ^\n' +
                    '"3" does not match "{}"\n' +
                    '"3" does not match "{}"')
        assert r.error.long_description == expected.format(1, 2) or expected.format(2, 1)

        assert not r.match('b')
        assert r.error.position == 1
        expected = ('Mismatch at 1:\n  b3\n   ^\n' +
                    'reached end of line but expected "{}"\n' +
                    'reached end of line but expected "{}"')
        assert r.error.long_description == expected.format(1, 2) or expected.format(2, 1)

    def test_flattening(self):
        r = OneOf(
            'a',
            'b',
            Rule(
                'c',
                Rule.with_name('d')('d')
            ))

        assert r.match('a')
        assert r.matched == 'a'

        assert r.match('b')
        assert r.matched == 'b'
        assert r.d.matched is None

        assert r.match('cd')
        assert r.matched == 'cd'
        assert r.d.matched == 'd'


class TestTokenRedefinitions:
    def test_sibling_redefinition(self):
        r = Rule(Rule.with_name('x')('a'), Rule.with_name('x')('b'))

        assert r.match('ab')
        assert r.x[0].matched == 'a'
        assert r.x[1].matched == 'b'

    def test_oneof_sibling_redefinition(self):
        r = OneOf(Rule.with_name('x')('a'), Rule.with_name('x')('b'))

        assert r.match('a')
        assert r.x[0].matched == 'a'
        assert r.x[1].matched is None

        assert r.match('b')
        assert r.x[0].matched is None
        assert r.x[1].matched == 'b'

    def test_child_redefinition(self):
        r = Rule.with_name('x')('a',
                                Rule.with_name('x')('b',
                                                    Rule.with_name('x')('c')))

        assert not r.match('a')
        assert r.error.position == 1

        assert r.match('abc')
        assert r.matched == 'abc'
        assert r.x.matched == 'bc'
        assert r.x.x.matched == 'c'

    def test_flattened(self):
        r = Rule(
                Rule.with_name('xx')('a'),
                Rule(
                    Rule.with_name('yy')('b'),
                    Optional(
                        Rule.with_name('xx')('c'))
                )
            )

        assert r.match('abc')
        assert r.xx[0].matched == 'a'
        assert r.yy.matched == 'b'
        assert r.xx[1].matched == 'c'

        assert r.match('ab')
        assert r.xx[0].matched == 'a'
        assert r.yy.matched == 'b'
        assert r.xx[1].matched is None


class TestGrammarClass:
    def test_example(self):

        class MorningGrammar(Grammar):
            person = OneOf('John', 'Peter', 'Ann', 'Paul', 'Rachel')
            who = Rule(person, Optional(', ', person), Optional(' and ', person))
            juice = Rule('juice')
            milk = Optional(' with milk')
            tea = Rule('tea', milk)
            what = OneOf(juice, tea)
            grammar = Rule(who, ' like', Optional('s'), ' to drink ', what, '\.')

        r = MorningGrammar.create()

        assert MorningGrammar.juice.name == 'juice'
        with raises(RuleNamingError):
            MorningGrammar.juice.name = ''

        assert r.match('Ann likes to drink tea with milk.')
        assert r.who.matched == 'Ann'
        assert r.what.matched == 'tea with milk'
        assert r.what.juice.matched is None
        assert r.what.tea.matched
        assert r.what.tea.milk.matched

        with raises(AttributeError):
            assert r.what.tea.sugar.matched

        assert r.match('Peter likes to drink tea.')
        assert r.who.matched == 'Peter'
        assert r.what.matched == 'tea'
        assert r.what.juice.matched is None
        assert r.what.tea.matched
        assert r.what.tea.milk.matched is None

        assert r.match('Peter, Rachel and Ann like to drink juice.')
        assert r.who.matched == 'Peter, Rachel and Ann'
        assert r.who.person[0].matched == 'Peter'
        assert r.who.person[1].matched == 'Rachel'
        assert r.who.person[2].matched == 'Ann'
        assert r.what.matched == 'juice'
        assert r.what.juice.matched is not None
        assert r.what.tea.matched is None

        assert not r.match('Peter likes to drink coffee.')
        assert r.error.position == 21

        assert not r.match('Peter likes to drink tea with lemon.')
        assert r.error.position == 24

    def test_empty_rules(self):
        class EmptyGrammar(Grammar):
            a = Rule('')
            b = Rule(a, a)
            c = OneOf(a, a, a)
            d = Optional(b)
            grammar = Rule(a, b, c, d)

        g = EmptyGrammar.create()
        assert g.match('')
        assert g.a.matched == ''
        assert g.b.matched == ''
        assert g.b.a[0].matched == ''
        assert g.b.a[1].matched == ''
        assert g.c.a[0].matched == ''
        assert g.c.a[1].matched is None
        assert g.c.a[2].matched is None
        assert g.d.matched == ''
        assert g.d.b.matched == ''
        assert g.d.b.a[0].matched == ''
        assert g.d.b.a[1].matched == ''


class TestAbstractClasses:
    """Test classes that are not supposed to be used directly."""

    def test_base_rule(self):
        r = BaseRule()
        with raises(NotImplementedError):
            r.match('')
        with raises(NotImplementedError):
            r.clone()

    def test_compound_rule(self):
        r = CompoundRule('r')
        with raises(NotImplementedError):
            r.match('')

        r = BaseCompoundRule('r')
        with raises(NotImplementedError):
            r.match('')
