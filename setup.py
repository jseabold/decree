from setuptools import setup, find_packages

setup(
    name='decree',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click'
    ],
    entry_points='''
        [console_scripts]
        decree=decree.cli.__main__:cli
    '''
)
