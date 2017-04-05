ruler
=====

Ruler is a lightweight regular expressions wrapper. Its aim is to make regex definitions more
modular, intuitive, readable and the mismatch reporting more informative.


Quick start
-----------

Let's implement the following grammar, given in EBNF_::

    grammar = who, ' likes to drink ', what;
    who = 'John' | 'Peter' | 'Ann';
    what = tea | juice;
    juice = 'juice';
    tea = 'tea', [milk];
    milk = ' with milk';

Using ruler it looks almost identical to EBNF_::

    class Morning(Grammar):
        who = OneOf('John', 'Peter', 'Ann')
        juice = Rule('juice')
        milk = Optional(' with milk')
        tea = Rule('tea', milk)
        what = OneOf(juice, tea)

        _grammar_ = Rule(who, ' likes to drink ', what, '\.')

Now it is possible to match the grammar:

>>> morning = Morning()
>>> match, error = morning.match('Ann likes to drink beer.')

``match`` method returns a tuple of two elements. The second element contains the information about
the match error, if the match failed, and the first element contains information about the successful
match. Naturally, one and only one of the two will be ``None``. In this case the string actually
fails to match:

>>> error is None
False
>>> match is None
True
>>> print(error.long_description)
Mismatch at 19:
  Ann likes to drink beer.
                     ^
"beer." does not match "juice"
"beer." does not match "tea"

Beer isn't one of the options in the grammar and the error message clearly pinpoints the mismatch
location and reason. Now let's try something that matches:

>>> match, error = morning.match('Ann likes to drink tea with milk.')
>>> match is None
False
>>> error is None
True
>>> match
<Match('Ann likes to drink tea with milk.', ['who', 'what']) at 0x3ecaa20>

Rules that were defined as the grammar members act as capture groups:

>>> str(match.who)
'Ann'
>>> str(match.what)
'tea with milk'
>>> bool(match.what.juice)
False
>>> bool(match.what.tea)
True
>>> bool(match.what.tea.milk)
True

Let's try another match:

>>> match, error = morning.match('Peter likes to drink juice. And nothing else matters.')
>>> str(match)
'Peter likes to drink juice.'
>>> str(match.who)
'Peter'
>>> bool(match.what.juice)
True
>>> bool(match.what.tea)
False

Matches implement implicit conversions to string and bool, they can also be compared to strings:

>>> if match:
        if match.who == 'Ann':
            print('Girls like', match.what)
        else:
            print('Boys like', match.what)
Boys like juice

The text inside the rules can be any valid regular expression. So we could rewrite our
grammar like this::

    class Morning(Grammar):
        who = Rule('\w+')
        juice = Rule('juice')
        milk = Optional(' with milk')
        tea = Rule('tea', milk)
        what = OneOf(juice, tea)

        _grammar_ = Rule(who, ' likes to drink ', what, '\.')

>>> morning = Morning()
>>> match, error = morning.match('R2D2 likes to drink juice. And nothing else matters.')
>>> str(match.who)
'R2D2'


Performance
-----------


Development
-----------

1. Tox takes care almost of everything without installing anything manually.
1. If tox is not enough then create a new virtualenv and ``pip install -r requirements_develop.txt``.
1. Dependencies are managed by adding them to ``reqs_*.dep`` files and running pip-compile + pip-sync.

TODO
----
::

    [X] TravisCI
    [X] tox/detox
    [ ] Sphinx
    [ ] Register on PyPI
    [ ] Upload to PyPI
    [x] flake8
    [ ] bumpversion
    [x] Landscape
    [ ] AppVeyor
    [ ] isort
    [ ] Performance benchmarking

.. _EBNF: https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form