from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = [line.strip() for line in fh.readlines() if line.strip() and not line.startswith("#")]

setup(
    name="android-reader",
    version="0.1.0",
    author="26lu",
    author_email="example@example.com",
    description="一款跨平台的Android设备数据读取工具，支持读取联系人、短信和照片",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/android-data-reader",
    packages=find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9,<3.10",
    entry_points={
        "console_scripts": [
            "android-reader=src.main:main",
        ],
    },
    package_data={
        "": ["*.md", "LICENSE"],
    },
    include_package_data=True,
)