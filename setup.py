from setuptools import setup

setup(
    name='sdr',
    version='0.1',
    py_modules=['sourcedrive'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        sdr=sourcedrive:sdr
    ''',
)