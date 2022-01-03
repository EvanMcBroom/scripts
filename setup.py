import re
import setuptools
import sys

for command in ['register', 'upload']:
    if command in sys.argv:
        print('Command {} is not allowed for this module.'.format(command))
        sys.exit(1)

with open('requirements.txt', 'r', encoding='utf-8') as file:
    # Match an valid requirement without matching a comment
    regex = re.compile(r'^\s*\w+(\s*[=<>]?=\s*[0-9.]+)?')
    install_requires = [regex.search(line) for line in file]

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
    package_dir={'': 'scripts'},
    packages=setuptools.find_packages(where='scripts'),
    python_requires='>=3.6',
    install_requires=install_requires,
    extras_require={
        'dev': ['check-manifest']
    },
    entry_points={
        'console_scripts': [
            'sserv=tool:main'
        ],
    },
)