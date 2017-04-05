from setuptools import setup, find_packages
from codecs import open
from os import path

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
# Get the installation requirements from install_requires.txt file
with open(path.join(here, 'reqs_install.dep'), encoding='utf-8') as f:
    install_requires = f.readlines()

setup(
    name='ruler',
    version='1.0.0.dev1',

    description='Modular regular expressions with practical mismatch reporting',
    long_description=long_description,
    url='https://github.com/yanivmo/ruler',
    author='Yaniv Mordekhay',
    author_email='yaniv@linuxmail.org',
    license='MIT',

    # Add all packages under src
    packages=find_packages('src'),
    # src is the root directory for all the packages
    package_dir={'': 'src'},

    install_requires=install_requires,

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
        'Programming Language :: Python :: 3.6',
    ],
    keywords='regex parsing grammar'
)
