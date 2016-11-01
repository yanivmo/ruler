from pytest import raises

import rulre


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
        r = rulre.Rule('a').name('r1')

        m = r.match('a')
        assert m.is_matching
        assert m.matching_text == 'a'
        assert m.remainder == ''
        assert m.tokens['r1'] == 'a'

        m = r.match('b')
        assert not m.is_matching
        assert m.error_position == 0, m.error_text

    def test_chained_simplest_rules(self):
        r = rulre.Rule('a', 'b', 'c').name('r1')

        m = r.match('abcdefg')
        assert m.is_matching
        assert m.matching_text == 'abc'
        assert m.remainder == 'defg'
        assert m.tokens['r1'] == 'abc'

        m = r.match('abdefg')
        assert not m.is_matching
        assert m.error_position == 2, m.error_text

    def test_nested_rules(self):
        r = rulre.Rule(
            'a',
            rulre.Rule(
                'b',
                rulre.Rule('c', 'd').name('r1.1.1')
            ).name('r1.1'),
            rulre.Rule('e').name('r1.2')
        ).name('r1')

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
        r = rulre.Optional('a')

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
        r = rulre.Rule(
            'a',
            rulre.Optional('b').name('r1.1'),
            rulre.Optional('c', 'd').name('r1.2'),
            'e'
        ).name('r1')

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
        r = rulre.OneOf('a', 'b', 'c').name('letter')

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
        r = rulre.OneOf(
            rulre.Rule('a').name('r1'),
            rulre.Rule('b', '1').name('r2'),
            rulre.Rule('b', '2').name('r3')
        ).name('one-of')

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
        r = rulre.Rule(
            rulre.Rule('a').name('A'),
            rulre.Rule('b').name('A')
        )

        m = r.match('a')
        assert not m.is_matching, m.error_text
        assert m.matching_text == 'a'
        assert m.error_position == 1
        assert m.tokens['A'] == 'a'

        with raises(rulre.TokenRedefinitionError):
            r.match('ab')

    def test_child_redefinition(self):
        r = rulre.Rule(
            rulre.Rule(
                'a',
                rulre.Rule('b').name('A')
            ).name('A')
        )

        m = r.match('a')
        assert not m.is_matching, m.error_text
        assert m.matching_text == 'a'
        assert m.error_position == 1

        with raises(rulre.TokenRedefinitionError):
            r.match('ab')

    def test_oneof(self):
        r = rulre.OneOf(
            rulre.Rule('a').name('A'),
            rulre.Rule('b').name('B'),
        ).name('A')

        m = r.match('bb')
        assert m.is_matching
        assert m.matching_text == 'b'
        assert m.remainder == 'b'
        assert m.tokens['B'] == 'b'
        assert m.tokens['A'] == 'b'

        with raises(rulre.TokenRedefinitionError):
            r.match('ab')


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
