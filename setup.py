from setuptools import setup, find_packages


classifiers = [
    # 'Development Status :: 5 - Production/Stable',
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'License :: OSI Approved :: BSD License',
]

install_requires = [
    'prompt-toolkit>=0.60',
    'pyserial>=3.0',
]

extras_require = {
    'tests': [
        'tox >= 2.6.0',
        'pytest >= 3.0.3',
        'pytest-cov >= 2.3.1',
    ],
    'devel': [
        'bumpversion >= 0.5.2',
        'check-manifest >= 0.35',
        'readme-renderer >= 16.0',
        'flake8',
        'pep8-naming',
    ]
}

kw = {
    'name':                 'grblcom',
    'version':              '0.0.0',

    'description':          'Rich serial-console client for GRBL',
    'long_description':     open('README.rst').read(),

    'author':               'Georgi Valkov',
    'author_email':         'georgi.t.valkov@gmail.com',
    'license':              'Revised BSD License',
    'keywords':             'grbl',
    'url':                  'https://github.com/gvalkov/grblcom',
    'classifiers':          classifiers,
    'install_requires':     install_requires,
    'extras_require':       extras_require,
    'packages':             find_packages(),
    'zip_safe':             True,
}


if __name__ == '__main__':
    setup(**kw)
