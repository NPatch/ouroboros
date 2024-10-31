from setuptools import setup, find_packages

setup(
    name='ouroboros',
    version='1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ouroboros=ouroboros.ouroboros:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.py'],
    },
)
