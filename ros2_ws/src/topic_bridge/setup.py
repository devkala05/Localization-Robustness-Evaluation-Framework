from setuptools import setup

package_name = "topic_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    install_requires=["setuptools", "PyYAML"],
    entry_points={"console_scripts": ["topic_bridge=topic_bridge.topic_bridge:main"]},
)
