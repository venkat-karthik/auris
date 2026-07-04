from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="auris-python",
    version="1.0.0",
    author="Auris Voice AI Platform",
    author_email="support@auris.ai",
    description="Official Python SDK for the Auris Enterprise Voice AI Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/venkat-karthik/auris",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
    ],
)
