# setup.py
from setuptools import setup, find_packages

setup(
    name="variatica-bot",
    version="2.0",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot==13.15',
        'pyyaml==6.0.3',
        'flask==2.3.3',
        'gunicorn==20.1.0',
        'python-dotenv==1.0.0',
        'requests==2.26.0',
        'urllib3==1.26.18',
    ],
    python_requires='>=3.8,<=3.11',
)
