from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='aligner',
    version='2.1',
    author='Tomek Fraczek',
    author_email='tfraczek@uw.edu',
    description='Manual Time Alignment of accelerometer data',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Weill-Neurohub-OPTiMaL/ManualTimeAlignerGUI',
    project_urls={
        "Bug Tracker": "https://github.com/Weill-Neurohub-OPTiMaL/ManualTimeAlignerGUI/issues"
    },
    license_files='LICENSE',
    packages=find_packages(),
    install_requires=['numpy', 'pandas', 'matplotlib', 'gitpython'],
)