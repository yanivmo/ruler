from setuptools import setup, find_packages
from codecs import open
from os import path

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rulre',
    version='1.0.0.dev01',

    description='Modular regular expressions with practical mismatch reporting',
    long_description=long_description,
    url='https://github.com/yanivmo/rulre',
    author='Yaniv Mordekhay',
    license='MIT',

    packages=find_packages(exclude=['docs', 'tests']),
    # install_requires=[''],

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',

        'Topic :: Software Development :: Libraries :: Python Modules',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='regex parsing grammar'
)
