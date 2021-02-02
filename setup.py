from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='python-crabber',
    version='0.2.4',
    description='A Python client for the Crabber REST API.',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Jake Ledoux',
    author_email='contactjakeledoux@gmail.com',
    url='https://github.com/jakeledoux/python-crabber',
    license='GNU General Public License v2.0',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'requests'
    ],
)
