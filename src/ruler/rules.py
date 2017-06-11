import re

from .base_rules import BaseRule, BaseCompoundRule


class Grammar(object):
    """
    Rules container.
    This class is intended to be inherited and contain all the rules of a grammar.
    The main purpose of the class is to name the rules and arrange them hierarchically.

    The inheriting class must assign the root rule to ``grammar`` attribute.
    """
    grammar = None

    @classmethod
    def create(cls):
        # Collect and name member rules
        for attr_name in dir(cls):

            # 'grammar' is a reserved name
            if attr_name == 'grammar':
                continue

            attr = getattr(cls, attr_name)
            if isinstance(attr, BaseRule):
                attr.name = attr_name

        cls.grammar.register_named_subrules()

        return cls.grammar.clone()


class CompoundRule(BaseCompoundRule):
    def __init__(self, *rules):
        super(CompoundRule, self).__init__(RegexRule, *rules)

    def match(self, text):
        raise NotImplementedError


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
                self._mismatch.set(text, mismatch_position, sub_rule.error.description)
                self.error = self._mismatch
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
            self._mismatch.set(text, 0, error_text)
            self.error = self._mismatch
            self.matched = None
            return False

    def clone(self):
        twin = RegexRule(self._regex_text)
        twin.name = self.name
        return twin

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
            self._mismatch.set(text, furthest_mismatch_position, description)
            self.error = self._mismatch
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
