from setuptools import setup

package_name = "orchestrator"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    install_requires=["setuptools", "numpy", "matplotlib", "PyYAML"],
    entry_points={"console_scripts": ["orchestrator=orchestrator.orchestrator:main"]},
)
