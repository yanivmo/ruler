import collections


class BaseRule(object):
    """
    The base class of all the rule types.
    """

    def __init__(self):
        self._name = ''
        self.matched = None
        self.error = None
        self._mismatch = Mismatch()

    def match(self, text):
        """
        Attempt to match the text.
        The results of the last match are storred in ``error`` and ``matched`` attributes.
        Each consecutive match overrides the previous results.
        :return: True if the match was successful, False otherwise.
        """
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
        """
        Make all the child rules, that have names, behave as member variables of
        their parent rules.
        """
        return {}

    def clone(self):
        """
        Create a new rule object having exactly the same name and matching conditions as self.
        :return: A new rule object of the same type as self.
        """
        raise NotImplementedError


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
            # If a rule has a name, the rule itself will be added as a named sub-rule;
            # if doesn't have a name, the named sub-rules of the rule will be added as
            # direct named sub-rules, skipping one level
            subrules = rule.register_named_subrules()
            if rule.name:
                subrules = {rule.name: rule}

            for name, subrule in subrules.items():
                existing = self._named_rules.get(name)
                # If more than one named sub-rule with the same name exist, the name
                # will actually reference a list of rules
                if existing:
                    if isinstance(existing, collections.MutableSequence):
                        existing.append(subrule)
                    else:
                        self._named_rules[name] = [existing, subrule]
                else:
                    self._named_rules[name] = subrule

        return self._named_rules

    def clone(self):
        twin = type(self)(*[rule.clone() for rule in self._rules])
        twin.name = self.name
        return twin

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
    """
    Describes matching error.
    """
    def __init__(self):
        self.text = ''
        self.position = -1
        self.description = ''

    def set(self, text, position, description):
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


class RuleNamingError(Exception):
    """Raised on an attempt to set a name to an already named rule"""
    def __init__(self, name):
        super(RuleNamingError, self).__init__("Trying to rename an already named rule " + name)
