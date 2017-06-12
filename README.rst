*****
Ruler
*****

.. image:: https://travis-ci.org/yanivmo/ruler.svg?branch=master
    :target: https://travis-ci.org/yanivmo/ruler
    :alt: Build status

.. image:: https://landscape.io/github/yanivmo/ruler/master/landscape.svg?style=flat
   :target: https://landscape.io/github/yanivmo/ruler/master
   :alt: Code Health

.. image:: https://coveralls.io/repos/github/yanivmo/ruler/badge.svg?branch=master
   :target: https://coveralls.io/github/yanivmo/ruler?branch=master


Ruler is a lightweight regular expressions wrapper aiming to make regex definitions more
modular, intuitive, readable and the mismatch reporting more informative.


Quick start
===========

Let's implement the following grammar, given in EBNF_::

    grammar = who, ' likes to drink ', what;
    who = 'John' | 'Peter' | 'Ann' | 'Paul' | 'Rachel';
    what = tea | juice;
    juice = 'juice';
    tea = 'tea', [milk];
    milk = ' with milk';

Using ruler it looks almost identical to EBNF_:

>>> class Morning(Grammar):
...     who = OneOf('John', 'Peter', 'Ann', 'Paul', 'Rachel')
...     juice = Rule('juice')
...     milk = Optional(' with milk')
...     tea = Rule('tea', milk)
...     what = OneOf(juice, tea)
...     grammar = Rule(who, ' likes to drink ', what, '\.')
...
... morning = Morning.create()

A member named ``grammar`` must be always present - it acts as the start rule.
Let's begin rather with a mismatch:

>>> morning.match('John likes to drink coffee')
False

``match()`` returns ``True`` if the match was successful and ``False`` otherwise.
One of the major advantages of ``ruler``, as opposed to working directly with regular expressions,
is the ability to know exactly what went wrong:

>>> print(morning.error.long_description)
Mismatch at 20:
  John likes to drink coffee
                      ^
"coffee" does not match "juice"
"coffee" does not match "tea"

Let's fix our text:

>>> morning.match('John likes to drink tea.')
True

Any rule that is declared as a member variable of your grammar class acts as a named capture group
arranged hierarchically. Use ``matched`` attribute to retrieve the text matched by a specific rule:

>>> morning.matched
'John likes to drink tea.'
>>> morning.who.matched
'John'
>>> morning.what.matched
'tea'

Branches of OneOf rules that didn't match and optional rules that didn't match have ``None`` as
their values making it easy to ask whether they matched:

>>> morning.what.juice.matched is None
True
>>> morning.what.tea.matched is None
False
>>> morning.what.tea.milk.matched is None
True

Rules can be reused multiple times. If the same rule appears multiple times under the same parent,
these rules are collected into a list:

>>> class Morning(Grammar):
...     person = OneOf('John', 'Peter', 'Ann', 'Paul', 'Rachel')
...     who = Rule(person, Optional(', ', person), Optional(' and ', person))
...     juice = Rule('juice')
...     milk = Optional(' with milk')
...     tea = Rule('tea', milk)
...     what = OneOf(juice, tea)
...     grammar = Rule(who, ' like', Optional('s'), ' to drink ', what, '\.')
...
... morning = Morning.create()
... morning.match('Peter, Rachel and Ann like to drink juice.')
True
>>> morning.who.matched
'Peter, Rachel and Ann'
>>> morning.who.person[0].matched
'Peter'
>>> morning.who.person[1].matched
'Rachel'
>>> morning.who.person[2].matched
'Ann'

Notice that, in the grammar above, ``person`` rule is never a direct child of ``who`` but still
is accessed as such. That is because when a rule hierarchy is built, a rule is placed under its
closest named ancestor.

Rules' string arguments may actually be any valid regular expression. So we could rewrite our
grammar like this:

>>> class Morning(Grammar):
...     who = OneOf('\w+')
...     juice = Rule('juice')
...     milk = Optional(' with milk')
...     tea = Rule('tea', milk)
...     what = OneOf(juice, tea)
...     grammar = Rule(who, ' likes to drink ', what, '\.')
...
... morning = Morning()
... morning.match('R2D2 likes to drink juice. And nothing else matters.')
True
>>> morning.matched
'R2D2 likes to drink juice.'
>>> morning.who.matched
'R2D2'


Performance
===========
The library is well optimized for fast matching. Nevertheless it is important to remember
that this is a Python wrapper of the regex library and as such can never outperform matching
directly using the regex library. Currently ruler measures approximately ten times slower
than ``re``.


Development
===========

* To run the tests::

    pytest tests

* To compare the performance to the re library::

    python performance/re_compare.py

* To run performance profiling of a specific method, ``Rule.match`` for example::

    python performance/profile.py Rule.match

  More than one method can be specified in the same command.

Tox
---
Tox takes care of everything without installing anything manually. There are two groups of tox
environments: ``py*-test`` and ``py*-profile``. The test environments run the unit tests while the
profile environments run the performance profiling scripts. If tox is not enough then a development
environment can be generated by creating a new virtualenv and then running
``pip install -r requirements_develop.txt``.


Dependency management
---------------------
For the development needs, there are three requirements files in the project's root directory:

- ``requirements_test.txt`` contains all the dependencies needed to run the unit tests,
- ``requirements_profile.txt`` contains all the dependencies needed to run the performance profiling,
- ``requirements_develop.txt`` contains the testing dependencies, the profiling dependencies and some additional
  dependencies used in development.

The requirements files mentioned above are not intended for manual editing. Instead they are managed
using `pip-tools`_. The process of updating the requirements is as follows:

#. Add, remove or update a dependency in one of the ``reqs_*.dep`` files:

   - Update ``reqs_install.dep`` if the dependency is needed for the regular installation by the end user,
   - Update ``reqs_test.dep`` if the dependency is needed to run the unit tests but is not necessary for the
     regular installation,
   - Update ``reqs_profile.dep`` if the dependency is needed to run the performance profiling but is not necessary
     for the regular installation,
   - Update ``reqs_develop.dep`` if the dependency is not in one of the previous categories.

#. Generate the requirements file running ``pip-compile``. The exact command is documented in the beginning of each
   requirements file.
#. Consider running ``pip-sync requirements_develop.txt``.

Notice that there is no need to edit ``setup.py`` - it will pull the dependencies by itself from ``reqs_install.dep``.


.. _EBNF: https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form
.. _pip-tools: https://github.com/jazzband/pip-tools