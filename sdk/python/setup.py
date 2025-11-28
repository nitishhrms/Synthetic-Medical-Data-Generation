"""
Setup configuration for SyntheticTrial Python SDK
"""

from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Python SDK for SyntheticTrial - Generate realistic synthetic clinical trial data"

setup(
    name="synthetictrial",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Python SDK for generating realistic synthetic clinical trial data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/synthetic-medical-data",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pandas>=1.5.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "synthetictrial=synthetictrial.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
