from setuptools import setup, findpackages
import os

lib_dir   = os.path.dirname(os.path.realpath(__file__))
reqs_path = lib_dir + '/requirements.txt'
reqs = []
if os.path.isfile(reqs_path):
    with open(reqs_path) as f:
        reqs = f.read().splitlines()

setup(
name="systrade",
version='0.0.1',
packages=findpackages(),
author='Peter Hawkins',
python_requires='>=3.6',
install_requires=reqs
)
