import os
import sys

try:
    from setuptools import setup
    from setuptools.command.test import test as Command
    setup
except ImportError:
    from distutils.core import setup
    from distutils.core import Command

import appengine_requests

if sys.argv[-1] == "publish":
    os.system('python setup.py sdist upload')
    sys.exit()


packages = [
    'appengine_requests',
]


class PyTest(Command):

    def finalize_options(self):
        Command.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='appengine_requests',
    version=appengine_requests.__version__,
    description='',
    author='Beau Lyddon',
    tests_require=['pytest'],
    cmdclass={'test': PyTest}
)
