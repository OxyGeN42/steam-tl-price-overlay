from setuptools import setup, find_packages

setup(
    name="steam-tl-price-overlay",
    version="3.0.0",
    author="OxyGeN42",
    description="Steam masaustu istemcisi icin canlı döviz kuru ile TL overlay sistemi",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OxyGeN42/steam-tl-price-overlay",
    py_modules=["Steam_tl_price_overlay"],
    install_requires=[
        "requests>=2.25.0",
        "websocket-client>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "steam-tl-overlay=Steam_tl_price_overlay:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
)
