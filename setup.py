from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="db-migrator",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A universal database migration tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/db-migrator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mysql-connector-python>=8.0.0",
        "psycopg2-binary>=2.9.0",
        "click>=8.0.0",
        "PyYAML>=6.0",
        "rich>=10.0.0",
        "tqdm>=4.60.0",
    ],
    entry_points={
        "console_scripts": [
            "db-migrate=db_migrator.cli.commands:cli",
        ],
    },
)