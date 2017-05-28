
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


class BaseCompoundRule(BaseRule):
    """
    The base class of all the rules composed of sub-rules.
    """
    def __init__(self, default_rule_type, *rules):
        super(BaseCompoundRule, self).__init__()

        self._named_rules = {}
        self._rules = []
        for rule in rules:
            if str(rule) == rule:
                self._rules.append(default_rule_type(rule))
            else:
                self._rules.append(rule)
        self.register_named_subrules()

    def match(self, text):
        raise NotImplementedError

    def reset_match(self):
        super(BaseCompoundRule, self).reset_match()
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
                redefined_keys = set(self._named_rules) & set(grandchild_rules)
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
