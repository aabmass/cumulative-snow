from setuptools import setup

setup(
    name="cumulative_snow",
    version="0.1",
    description="Graph cumulative snow from NOAA data",
    url="https://github.com/aabmass/cumulative-snow",
    author="aabmass",
    author_email="aabmass@gmail.com",
    license="MIT",
    packages=["cumulative_snow"],
    zip_safe=False,
    install_requires=["numpy", "matplotlib", "pandas", "pyqt5",],
    entry_points={"console_scripts": ["cumulative_snow=cumulative_snow.main:main"]},
)
