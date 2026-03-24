from setuptools import setup, find_packages
import os

# Read long description from README if it exists
long_description = ""
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name="lockr",
    version="0.1.0",
    author="Lockr Team",
    author_email="hello@lockr.dev",
    description="Git-style secrets manager with post-quantum encryption and automated SOC-2 compliance reports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/balakumaran1507/Lockr",
    project_urls={
        "Bug Tracker": "https://github.com/balakumaran1507/Lockr/issues",
        "Documentation": "https://github.com/balakumaran1507/Lockr#readme",
        "Source Code": "https://github.com/balakumaran1507/Lockr",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="secrets security encryption vault compliance soc2 iso27001 post-quantum",
    python_requires=">=3.11",
    packages=find_packages(include=["cli*", "server*", "intent*"]),
    install_requires=[
        "fastapi>=0.111,<1.0",
        "uvicorn[standard]>=0.29,<1.0",
        "click>=8.1,<9.0",
        "rich>=13.7,<14.0",
        "cryptography>=42.0,<43.0",
        "httpx>=0.27,<1.0",
        "pydantic>=2.0,<3.0",
        "reportlab>=4.0,<5.0",  # For PDF compliance reports
        "toml>=0.10.2",  # For config parsing
    ],
    extras_require={
        "pq": ["liboqs-python>=0.10"],  # Post-quantum cryptography (requires liboqs)
        "dev": [
            "pytest>=8.0,<9.0",
            "pytest-asyncio>=0.23,<1.0",
            "pytest-cov>=4.1,<5.0",
            "black>=24.0,<25.0",
            "ruff>=0.3,<1.0",
            "mypy>=1.9,<2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lockr=cli.lockr:cli",
        ],
    },
)
