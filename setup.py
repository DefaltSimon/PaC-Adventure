# coding=utf-8
from setuptools import setup

def readme():
	with open("README.md", "r") as f:
		return f.read()

requirements = []
with open('requirements.txt') as f:
	requirements = f.read().splitlines()

setup(name='pac',
	  version='0.3',
	  description='A library for creating a text-based story.',
	  long_description=readme(),
	  classifiers=[
		'Development Status :: 4 - Beta',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3.5',
		'Topic :: Games/Entertainment :: Puzzle Games',
		'Intended Audience :: Developers',
	  ],
	  url='https://github.com/DefaltSimon/PaC-Adventure',
	  author='DefaltSimon',
	  license='MIT',
	  keywords='point and click defaltsimon adventure creator',
	  packages=['pac'],
	  install_requires=requirements,
	  zip_safe=True)