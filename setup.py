from setuptools import setup, find_packages

setup(
    name="dfs-optimizer",
    version="2.0.0",
    description="Professional MLB DFS Optimizer with ML Integration",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "pulp>=2.6.0",
        "requests>=2.26.0",
        "beautifulsoup4>=4.10.0",
        "PyQt5>=5.15.0",
        "scikit-learn>=1.0.0",
    ],
    python_requires=">=3.8",
)
