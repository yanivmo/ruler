"""
Grammar parsing library

- Tokens are returned up to the failing rule;
- Reports precise error position and the failure reason
"""

# TODO: Consider adding empty optional matches as None (similarly to OneOf)
# TODO: Consider adding automatic match comparison with strings
# TODO: Consider adding default root rule
# TODO: Change six

import re
import six
from builtins import object


class Grammar(object):
    def __init__(self, rule=None):
        # Collect and name member rules
        for attr_name in dir(self):
            attr = self.__getattribute__(attr_name)
            if isinstance(attr, BaseRule):
                attr.name = attr_name

        if rule:
            self._root_rule = rule
        elif '_grammar_' in dir(self):
            # noinspection PyUnresolvedReferences
            self._root_rule = self._grammar_

    def match(self, text):
        return self._root_rule.match(text)


class BaseRule(object):
    """
    The base class of all the rule types.
    """

    def __init__(self):
        self._name = ''

    def match(self, text):
        raise NotImplementedError

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, rule_name):
        if self._name and self._name != rule_name:
            raise RuleNamingError(self._name)
        self._name = rule_name


class CompoundRule(BaseRule):
    """
    The base class of all the rules composed of sub-rules.
    """
    def __init__(self, *rules):
        super(CompoundRule, self).__init__()

        self._rules = []
        for rule in rules:
            if str(rule) == rule:
                self._rules.append(RegexRule(rule))
            else:
                self._rules.append(rule)

    def match(self, text):
        raise NotImplementedError

    @classmethod
    def with_name(cls, rule_name):
        def factory(*rules):
            rule = cls(*rules)
            rule.name = rule_name
            return rule
        return factory

    @classmethod
    def _build_match(cls, matched_text, sub_rule_matches):
        """
        Match object factory.
        :param matched_text: The text that was matched.
        :param sub_rule_matches: A list of pairs mapping sub-rule objects to their matches.
        :return: A tuple (Match, None)
        """
        matches = {}
        for rule, match in sub_rule_matches:
            if rule.name:
                # The sub-rule has a name, add its match as my sub-match
                if rule.name in matches:
                    raise TokenRedefinitionError(rule.name)
                else:
                    matches[rule.name] = match
            elif match:  # match is allowed to be None here
                # The sub-rule doesn't have a name, add its sub-matches as my own sub-matches
                for rule_name, sub_match in match:
                    if rule_name in matches:
                        raise TokenRedefinitionError(rule_name)
                    else:
                        matches[rule_name] = sub_match

        return Match(matched_text, matches), None


class Rule(CompoundRule):
    """
    This rule matches if all of its sub-rules match.
    """
    def match(self, text):
        text_to_match = text
        sub_rule_matches = []

        # Advance through the text, matching each iteration the next rule
        for sub_rule in self._rules:
            # Try to match the next rule
            match, mismatch = sub_rule.match(text_to_match)

            if mismatch:
                mismatch_position = len(text) - len(text_to_match) + mismatch.position
                return None, Mismatch(mismatch_position, mismatch.description)
            else:
                # Remove the matched part from the text
                text_to_match = text_to_match[len(match):]
                sub_rule_matches.append((sub_rule, match))

        matched_text = text[:-len(text_to_match)] if text_to_match else text
        return self._build_match(matched_text, sub_rule_matches)


class RegexRule(BaseRule):
    """
    A rule defined using a regular expression.
    """
    def __init__(self, regex):
        super(RegexRule, self).__init__()

        self._regex_text = regex
        self._regex = re.compile(regex)

    def match(self, text):
        m = self._regex.match(text)
        if m:
            return Match(m.group(), {}), None
        else:
            return None, Mismatch(0, '"{}" does not match "{}"'.format(text, self._regex.pattern))


class OneOf(CompoundRule):
    """
    This rule matches if one of its sub-rules matches.
    """
    def match(self, text):
        matches = []
        mismatches = []
        matched_text = None
        furthest_mismatch_position = 0

        for sub_rule in self._rules:
            # If already matched, just write down the names
            if matched_text:
                matches.append((sub_rule, None))
            else:
                match, mismatch = sub_rule.match(text)

                if match:
                    matched_text = str(match)
                    matches.append((sub_rule, match))
                else:
                    matches.append((sub_rule, None))
                    mismatches.append(mismatch)
                    if mismatch.position > furthest_mismatch_position:
                        furthest_mismatch_position = mismatch.position

        if matched_text:
            return self._build_match(matched_text, matches)
        else:
            description = '\n'.join(set(
                [m.description for m in mismatches if m.position == furthest_mismatch_position]))
            return None, Mismatch(furthest_mismatch_position, description)


class Optional(Rule):
    """
    An optional rule.
    """
    def __init__(self, *rules):
        super(Optional, self).__init__(*rules)

    def match(self, text):
        match, mismatch = super(Optional, self).match(text)
        if mismatch:
            return Match('', {}), None
        else:
            return match, None


class Match(object):

    def __init__(self, text, sub_matches):
        self._text = text
        self._sub_matches = sub_matches  # type: dict

    def __str__(self):
        return self._text

    def __len__(self):
        return len(self._text)

    def __bool__(self):
        """
        Always True in boolean expressions. If this method is not defined, __len__ will be used,
        meaning the object will be evaluated as False for empty matches.
        """
        return True

    def __getattr__(self, item):
        if item in self._sub_matches:
            return self._sub_matches[item]
        else:
            raise AttributeError(item)

    def __iter__(self):
        return six.iteritems(self._sub_matches)


class Mismatch(object):
    def __init__(self, position, description):
        self.position = position
        self.description = description


class TokenRedefinitionError(Exception):
    """Raised if a grammar contains multiple tokens with the same name"""
    def __init__(self, token_name):
        super(TokenRedefinitionError, self).__init__(token_name)


class RuleNamingError(Exception):
    """Raised on an attempt to set a name to an already named rule"""
    def __init__(self, name):
        super(RuleNamingError, self).__init__("Trying to rename an already named rule " + name)
