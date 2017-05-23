"""
Grammar parsing library

- Tokens are returned up to the failing rule;
- Reports precise error position and the failure reason
- Intuitive syntax
"""

import re
# import six


class Grammar(object):
    def __init__(self, rule=None):
        self.matched = None
        self.error = None
        self._root_rule = None

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

        self._root_rule.register_named_subrules()

    def match(self, text):
        result = self._root_rule.match(text)
        self.matched = self._root_rule.matched
        self.error = self._root_rule.error
        return result


class BaseRule(object):
    """
    The base class of all the rule types.
    """

    def __init__(self):
        self._name = ''
        self.matched = None
        self.error = None

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

    def reset_match(self):
        self.matched = None
        self.error = None

    def register_named_subrules(self):
        return {}


class CompoundRule(BaseRule):
    """
    The base class of all the rules composed of sub-rules.
    """
    def __init__(self, *rules):
        super(CompoundRule, self).__init__()

        self._named_rules = {}
        self._rules = []
        for rule in rules:
            if str(rule) == rule:
                self._rules.append(RegexRule(rule))
            else:
                self._rules.append(rule)
        self.register_named_subrules()

    def match(self, text):
        raise NotImplementedError

    def reset_match(self):
        super(CompoundRule, self).reset_match()
        for rule in self._rules:
            rule.reset_match()

    def register_named_subrules(self):
        self._named_rules = {}

        for rule in self._rules:
            grandchild_rules = rule.register_named_subrules()
            if rule.name:
                if rule.name in self._named_rules:
                    raise TokenRedefinitionError(self, rule.name)
                else:
                    self._named_rules[rule.name] = rule
            else:
                redefined_keys = self._named_rules.keys() & grandchild_rules.keys()  # TODO: 2/3
                if redefined_keys:
                    raise TokenRedefinitionError(self, redefined_keys)
                else:
                    self._named_rules.update(grandchild_rules)
        return self._named_rules

    @classmethod
    def with_name(cls, rule_name):
        def factory(*rules):
            rule = cls(*rules)
            rule.name = rule_name
            return rule
        return factory

    def __getattr__(self, item):
        """
        Named sub-matches act as member variables.
        """
        if item in self._named_rules:
            return self._named_rules[item]
        else:
            raise AttributeError(item)

    def __repr__(self):
        return '{}(name={}, matched={}, rules={})'.format(
            self.__class__.__name__,
            repr(self._name),
            repr(self.matched),
            repr(self._rules)
        )


class Rule(CompoundRule):
    """
    This rule matches if all of its sub-rules match.
    """
    def match(self, text):
        text_to_match = text

        # Advance through the text, matching each iteration the next rule
        for sub_rule in self._rules:
            # Try to match the next rule
            if sub_rule.match(text_to_match):
                # Optional rules return True but might match None
                if sub_rule.matched is not None:
                    # Remove the matched part from the text
                    text_to_match = text_to_match[len(sub_rule.matched):]
            else:
                mismatch_position = len(text) - len(text_to_match) + sub_rule.error.position
                self.error = Mismatch(text, mismatch_position, sub_rule.error.description)
                self.matched = None
                return False

        self.error = None
        self.matched = text[:-len(text_to_match)] if text_to_match else text
        return True


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
            self.error = None
            self.matched = m.group()
            return True
        else:
            if text:
                error_text = '"{}" does not match "{}"'.format(text, self._regex.pattern)
            else:
                error_text = 'reached end of line but expected "{}"'.format(self._regex.pattern)
            self.error = Mismatch(text, 0, error_text)
            self.matched = None
            return False

    def __repr__(self):
        return '{}(name={}, matched={}, regex={})'.format(
            self.__class__.__name__,
            repr(self._name),
            repr(self.matched),
            repr(self._regex_text)
        )


class OneOf(CompoundRule):
    """
    This rule matches if one of its sub-rules matches.
    """
    def match(self, text):
        self.matched = None

        # Iterate until the first match
        sub_rules = iter(self._rules)
        for sub_rule in sub_rules:
            if sub_rule.match(text):
                self.matched = sub_rule.matched
                self.error = None
                break

        # Reset the matches of the remaining rules
        for sub_rule in sub_rules:
            sub_rule.reset_match()

        if self.matched is not None:
            return True
        else:
            furthest_mismatch_position = max((r.error.position for r in self._rules))
            description = '\n'.join(
                set((
                    r.error.description
                    for r in self._rules
                    if r.error.position == furthest_mismatch_position
                ))
            )
            self.error = Mismatch(text, furthest_mismatch_position, description)
            return False


class Optional(Rule):
    """
    An optional rule.
    """
    def __init__(self, *rules):
        super(Optional, self).__init__(*rules)

    def match(self, text):
        if not super(Optional, self).match(text):
            self.error = None
            self.matched = None
        return True


class Mismatch(object):
    def __init__(self, text, position, description):
        self.text = text
        self.position = position
        self.description = description

    @property
    def long_description(self):
        return 'Mismatch at {position}:\n  {text}\n  {marker_indent}^\n{description}'.format(
            position=self.position,
            text=self.text,
            marker_indent=' ' * self.position,
            description=self.description
        )


class TokenRedefinitionError(Exception):
    """Raised if a grammar contains multiple tokens with the same name"""
    def __init__(self, rule, token_name):
        super(TokenRedefinitionError, self).__init__('"{}" in {}'.format(token_name, repr(rule)))


class RuleNamingError(Exception):
    """Raised on an attempt to set a name to an already named rule"""
    def __init__(self, name):
        super(RuleNamingError, self).__init__("Trying to rename an already named rule " + name)
