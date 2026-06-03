from setuptools import setup

package_name = "perturbation_injector"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    install_requires=["setuptools", "numpy", "PyYAML"],
    entry_points={
        "console_scripts": [
            "sensor_perturbation_node=perturbation_injector.sensor_perturbation_node:main",
        ],
    },
)
