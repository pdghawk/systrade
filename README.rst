systrade - A simple package for systematic trading and testing
================================================================

systrade is a personal project in developing a package for the development of
trading strategies and backtesting them. The main aims of the project at this
stage in its development being for me to gain understanding of both the topic,
and furthering my software development skills. My career as a physicist often
focussed more on the mathematical elements of the problem at hand with quite
procedural code - developing better skills in developing design patterns, writing
unit tests etc was a key element of this project with many moving parts. This
project is in the early stages, so far focussing on building software that will
allow for easy extension to more complicated strategies, and backtesting systems.

The current implementation focusses on technical analysis models, using technical
indicators, and signals made of these indicators, to build trading strategies.
Parameters of a strategy, and parameters of the signals that form it, and indeed
indicators that form those, can all be accessed and adjusted easily via the
strategy itself. This is done using ideas from the design of scikit-learn:
API design for machine learning software: experiences from the scikit-learn
project, Buitinck et al., 2013. which can be found on the arXiv: https://arxiv.org/abs/1309.0238
(Note that this project is in no way endorsed by scikit-learn, and that the
original BSD license and copyright of scikit-learn is repeated in the relevant
module: systrade/models/base.py)

Backtesting of a strategy over many parameter sets can then be easily achieved,
with adjusted p values, and strategies passing the test for a given family-wise
error rate significance level.

Monte Carlo methods for generating stock pathways is also provided. This could
also form this basis for backtesting on 'alternate histories'. Ideas from the
following book:

C++ Designs Patterns and Derivatives Pricing, M.S. Joshi (Cambridge University Press)

were used in developing the systrade/monte subpackage.

An example use case can be found in notebooks/example.ipynb
