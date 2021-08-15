#!/usr/bin/env python3

import os
import setuptools

package_name = 'vacdec'

f = open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8')
readme = f.read()
f.close()

setuptools.setup(
    name=package_name,
    version="0.0.1",
    description="Decode the EU Covid-19 vaccine certificate",
    long_description=readme,
    long_description_content_type='text/markdown',
    author="Hanno Böck",
    author_email='hanno@hboeck.de',
    url='https://github.com/hannob/vacdec',
    packages=[],
    scripts=['vacdec'],
    python_requires='>=3',
    install_requires=[
        'base45',
        'cbor2',
        'pillow',
        'pyzbar'
    ],
    license="CC0",
    zip_safe=True,
    keywords=['vaccine'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
