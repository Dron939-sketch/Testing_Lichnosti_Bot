from setuptools import setup, find_packages

setup(
    name="variatica-bot",
    version="2.0",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot>=21.0,<22.0',
        'pyyaml>=6.0',
        'python-dotenv>=1.0',
        'flask>=2.3',
        'gunicorn>=21.0',
        'requests>=2.31',
        'aiohttp>=3.9',
    ],
    python_requires='>=3.8',
)
