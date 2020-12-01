#!/usr/bin/env python

import os
from setuptools import setup

directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(directory, 'README.md'), encoding='utf-8') as f:
  long_description = f.read()

setup(name='micromath',
      version='0.0.1',
      description='Microservice architecture for 3 math operations: exponentiation, fibonacci and factorial',
      author='Andrei Marin',
      license='MIT',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages = ['micromath'],
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
      ],
      install_requires=['docker-compose'],
      python_requires='>=3.6',
      include_package_data=True)
