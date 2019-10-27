import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="bluebees",
    version="1.0.10",
    description="Bluetooth Mesh Config Tools",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/matheuswhite/bluebees",
    author="Matheus White",
    author_email="tenoriomatheus0@gmail.com",
    license="GPL3",
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pycryptodome==3.7.3",
        "termcolor==1.1.0",
        "pyserial==3.4",
        "ecdsa==0.13",
        "ruamel.yaml==0.15.94",
        "pyzmq==18.0.1",
        "asyncserial==0.1.0",
        "pytest==4.5.0",
        "codecov==2.0.15",
        "pytest-cov==2.7.1",
        "click==7.0",
        "tqdm==4.32.1",
        "dataclasses==0.6"
    ],
    entry_points={
        "console_scripts": [
            "bluebees=bluebees.__main__:cli",
        ]
    },
)