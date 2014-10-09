__email__ = "nicolas.maire@unibas.ch"
__status__ = "Alpha"

from setuptools import setup, find_packages

setup(
    name='Su2',
    version='0.3',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask', 'Flask-AutoIndex', 'lxml', 'MySQL-python', 'simplekml', 'xlwt', 'gunicorn']
)






