from setuptools import setup


setup(
    name="adapter-hub-cli",
    version="1.0.0",
    author="The AdapterHub Team",
    author_email="calpt@mail.de",
    description="Command-line tools for checking and packaging adapters for the AdapterHub",
    keywords="NLP deep-learning transformers adapters adapterhub",
    license="MIT",
    url="https://adapterhub.ml",
    package_dir={"adapter_hub_cli": "cli", "adapter_hub_cli.utils": ""},
    packages=["adapter_hub_cli", "adapter_hub_cli.utils"],
    install_requires=[
        "adapter-transformers",
        # for pack
        "colorama",
        "PyInquirer",
        "ruamel.yaml",
        # for check
        "jsonschema",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "adapter-hub-cli=adapter_hub_cli:main",
        ]
    },
    python_requires=">=3.6.0",
)
