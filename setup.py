# coding=utf-8
from setuptools import setup, find_packages


def readme():
    with open("README.md", "r") as f:
        return f.read()


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='pac',
      version='0.3',
      description='A library for creating a text-based story.',
      long_description=readme(),
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',

          'Topic :: Games/Entertainment :: Puzzle Games',
          'Intended Audience :: Developers',

          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
      ],
      url='https://github.com/DefaltSimon/PaC-Adventure',
      author='DefaltSimon',
      license='MIT',
      keywords='point and click defaltsimon adventure creator',
      packages=find_packages(exclude=["docs", "test"]),
      install_requires=requirements
      )
