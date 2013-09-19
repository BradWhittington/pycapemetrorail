from setuptools import setup, find_packages
import os
import platform

DESCRIPTION = 'Library to access and parse Cape Metro Rail train schedules'

LONG_DESCRIPTION = None
try:
    LONG_DESCRIPTION = open('README.rst').read()
except:
    pass

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    name='cape-metrorail',
    version='0.1',
    packages=['cape_metrorail'],
    author='Bradley Whittington',
    author_email='radbrad182@gmail.com',
    url='http://github.com/bradwhittington/capemetrorail/',
    license='MIT',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'mechanize==0.2.5',
        'clint',
        'BeautifulSoup==3.2.1',
        'tablib',
    ],
)

