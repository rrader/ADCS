from setuptools import setup

setup(
    name='adcs-machine-cad',
    version='0.1',
    author='Roman Rader',
    author_email='roman.rader@gmail.com',
    install_requires=['pydot'],
    tests_require=['nose'],
    packages=[
        'adcs',
    ],
    entry_points={
        'console_scripts': [
            'adcs = adcs.main:main',
        ]
    }
)
