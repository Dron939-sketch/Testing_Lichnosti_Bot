from setuptools import setup, find_packages

setup(
    name="variatica-bot",
    version="2.0",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot>=20.0,<21.0',
        'pyyaml>=6.0',
        'python-dotenv>=1.0',
        'flask>=2.3',
        'gunicorn>=20.0',
        'requests>=2.31',
    ],
    python_requires='>=3.8,<3.13',
)
