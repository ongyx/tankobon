from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    install_requires = f.read().split("\n")

setup(
    name="kopiccino",
    version="1.0.0a0",
    author="Ong Yong Xin",
    author_email="ongyongxin2020+github@gmail.com",
    description="A manga downloader by scraping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/onyxware/manhua",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    python_requires=">=3.6",
    install_requires=install_requires,
)
