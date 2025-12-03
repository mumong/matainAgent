"""
项目安装配置文件
安装方式: pip install -e .
"""
from setuptools import setup, find_packages

setup(
    name="matain-agent",
    version="0.1.0",
    description="Matain Agent - AI Agent Framework",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
    ],
    python_requires=">=3.10",
)

