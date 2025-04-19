# Standard package setup
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='pdg',
    version='0.2.0',
    author='Particle Data Group',
    author_email='jberinger@lbl.gov',
    description='Python API for accessing PDG data',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://pdg.lbl.gov',
    license='Modified BSD',
    packages=find_packages(),
    package_data={"pdg": ["pdg.sqlite"]},
    install_requires=['SQLAlchemy>=1.4'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Database :: Front-Ends',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Physics'
        ],
    keywords='PDG, particle physics',
    project_urls={
        'Documentation': 'https://pdgapi.lbl.gov/doc/',
        'GitHub': 'https://github.com/particledatagroup/api',
        'Changelog': 'https://github.com/particledatagroup/api/blob/main/CHANGELOG.md'
    },
)
