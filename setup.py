from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='mwm',
    version='0.9.0',
    author='Ilya Zverev',
    author_email='ilya@zverev.info',
    packages=['mwm'],
    url='http://pypi.python.org/pypi/mwm/',
    license='Apache License 2.0',
    description='Library to read binary MAPS.ME files.',
    long_description=open(path.join(here, 'README.md')).read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)
