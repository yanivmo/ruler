"""
Grammar parsing library

- Tokens are returned up to the failing rule;
- Reports precise error position and the failure reason
"""

import re


class Rule(object):
    """
    This rule matches if all of its sub-rules match.
    """

    def __init__(self, name=''):
        self._name = name
        self._rules = []

    def defined_as(self, *rules):
        """Define the rule expression"""
        for rule in rules:
            if str(rule) == rule:
                self._rules.append(RegexRule(rule))
            else:
                self._rules.append(rule)
        return self

    @property
    def rule_structure(self):
        return self._name, [r.rule_structure for r in self._rules]

    def match(self, text):
        text_to_match = text
        result = MatchResult()

        # Advance through the text, matching each iteration the next rule
        for subrule in self._rules:
            # Try to match the next rule
            subrule_match = subrule.match(text_to_match)  # type: MatchResult
            result.tokens.update(subrule_match.tokens)

            if subrule_match.is_matching:
                # What is left after the current rule will be matched against the next rule
                text_to_match = subrule_match.remainder  # type: str
                # Track position in case we encounter an error
                result.error_position += len(subrule_match.matching_text)
            else:
                result.is_matching = False
                result.error_position += subrule_match.error_position
                result.error_text = subrule_match.error_text
                break

        if result.is_matching:
            result.matching_text = text[:-len(text_to_match)] if text_to_match else text
            result.remainder = text_to_match

            if self._name:
                if self._name in result.tokens:
                    raise GrammarTokenRedefiition(self._name)
                result.tokens[self._name] = result.matching_text
        else:
            result.matching_text = text[:result.error_position]
            result.remainder = text[result.error_position:]
        return result


class RegexRule(object):
    """
    A rule defined using a regular expression.
    """

    def __init__(self, regex):
        self._regex_text = regex
        self._regex = re.compile(regex)

    @property
    def rule_structure(self):
        return self._regex_text

    def match(self, text):
        m = self._regex.match(text)
        if m:
            return MatchResult(
                is_matching=True,
                matching_text=m.group(),
                remainder=text[m.end():],
            )
        else:
            return MatchResult(
                is_matching=False,
                remainder=text,
                error_text='"{}" does not match "{}"'.format(text, self._regex.pattern),
                error_position=0
            )


class OneOf(object):
    """
    This rule matches if one of its sub-rules matches.
    """

    def __init__(self, *rules):
        self._rules = []
        for rule in rules:
            if str(rule) == rule:
                self._rules.append(RegexRule(rule))
            else:
                self._rules.append(rule)

    @property
    def rule_structure(self):
        return [r.rule_structure for r in self._rules]

    def match(self, text):
        failures = []
        furthest_failure_position = 0

        for subrule in self._rules:
            result = subrule.match(text)

            if result.is_matching:
                return result
            else:
                failures.append(result)
                if result.error_position > furthest_failure_position:
                    furthest_failure_position = result.error_position

        # None of the rules matched
        return MatchResult(
            is_matching=False,
            matching_text=text[:furthest_failure_position],
            remainder=text[furthest_failure_position:],
            tokens={},
            error_position=furthest_failure_position,
            error_text='\n'.join(set([e.error_text for e in failures if e.error_position == furthest_failure_position]))
        )


class Optional(Rule):
    """
    An optional rule.
    """

    def __init__(self, name=''):
        super().__init__(name)

    def defined_as(self, *rules):
        super().defined_as(*rules)
        return self

    def match(self, text):
        result = super().match(text)
        if not result.is_matching:
            result.is_matching = True
            result.matching_text = ''
            result.remainder = text
            result.tokens = {}
            result.error_text = ''
            result.error_position = 0
        return result


class MatchResult(object):
    """
    Describes a result of a rule application.
    Attributes:
        - is_matching    - True if the text matches the rule
        - matching_text  - The portion of the text that matched the rule
        - remainder      - The remaining text that was not consumed by the rule
        - tokens         - A dictionary of tokens matched by the rule
        - error_text     - Error message if there was no match
        - error_position - The position in the text that caused the match failure
    """
    def __init__(self, **kwargs):
        self.is_matching = True
        self.matching_text = ''
        self.remainder = ''
        self.tokens = {}
        self.error_text = ''
        self.error_position = 0

        for key, value in kwargs.items():
            self.__dict__[key] = value


class GrammarTokenRedefiition(Exception):
    """Raised if a grammar contains multiple tokens with the same name"""
    def __init__(self, token_name):
        super().__init__(token_name)
