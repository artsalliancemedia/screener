from distutils.core import setup
from screener import __version__

setup(
    name = 'screener',
    version = __version__,
    description = 'A DCI media server emulator',
    author = 'Arts Alliance Media',
    author_email = 'dev@artsalliancemedia.com',
    url = 'http://www.artsalliancemedia.com',
    packages = ('screener',),
    requires = ('klv', 'twisted', 'smpteparsers'),
    extras_require = {"docs": ("sphinx",)}
)