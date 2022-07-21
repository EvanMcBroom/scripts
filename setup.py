import os
import re
import setuptools
import sys

for command in ['register', 'upload']:
    if command in sys.argv:
        print('Command {} is not allowed for this module.'.format(command))
        sys.exit(1)

path = os.path.dirname(os.path.abspath(__file__))
with open('{}/requirements.txt'.format(path), 'r', encoding='utf-8') as file:
    # Match an valid requirement without matching a comment
    install_requires = re.findall(r'^[^#].*$', file.read(), re.MULTILINE)

setuptools.setup(
    name='scripts',
    author='Evan McBroom',
    description='Utility code for *nix boxes.',
    url='https://github.com/EvanMcBroom/scripts',
    project_urls={
        'Documentation': 'https://github.com/EvanMcBroom/scripts',
        'Bug Reports': 'https://github.com/EvanMcBroom/scripts/issues',
        'Source Code': 'https://github.com/EvanMcBroom/scripts/tree/master/scripts'
    },
    packages=setuptools.find_packages(where=path),
    python_requires='>=3.6',
    install_requires=install_requires,
    extras_require={
        'dev': ['check-manifest']
    },
    entry_points={
        'console_scripts': [
            'bhq=scripts.bhquery:main',
            'scan=scripts.scan:main',
            'sserv=scripts.https:main',
            'urlparse=scripts.urlparse:main'
        ],
    },
)