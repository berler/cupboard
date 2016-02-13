from setuptools import setup
import re

version = ''
with open('cupboard.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
    name = 'cupboard',
    version = version,
    py_modules = ['cupboard'],
    author = 'Steven Berler',
    author_email = 'berler@gmail.com',
    description = 'Cupboard is an alternative to shelve which uses an sqlite db and json for serialization',
    license = 'MIT',
    )
