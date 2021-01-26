from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='python-crabber',
    version='0.1.0',
    description='A Python client for the Crabber REST API.',
    long_description=readme,
    author='Jake Ledoux',
    author_email='contactjakeledoux@gmail.com',
    url='https://github.com/jakeledoux/python-crabber',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
