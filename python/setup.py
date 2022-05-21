import setuptools
import os


def get_description():
    if os.path.isfile("README.md"):
        with open("README.md", "r") as fh:
            desc = fh.read()
    else:
        desc = ""
    return desc


setuptools.setup(
    name="credict",
    version="0.1.2",
    description="Python interface for Credict smart contracts on Ethereum.",
    long_description=get_description(),
    long_description_content_type="text/markdown",
    author="Pavel",
    author_email="pavelhurwicz@gmail.com",
    url="https://github.com/phurwicz/credict-py",
    packages=setuptools.find_packages(include=["credict*"]),
    install_requires=[
        # utilities
        "pandas>=1.4.0",
        "tqdm>=4.0",
        "rich>=11.0.0",
        "deprecated>=1.1.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
