from setuptools import setup, find_packages

setup(
    name="eeg_uhb",
    version="0.1.0",
    description="Librería modular para adquisición y procesamiento EEG de UHB",
    author="Amaury Santiago Horta",
    author_email="asantiagoh2300@alumno.ipn.mx",
    url="https://github.com/IngAmaury/EEG_UHB_LIBRARY",
    packages=find_packages(),
    install_requires=[
        "numpy==1.26.4",
        "pylsl==1.15.0",
        "scipy==1.13.1",
        "scikit-fuzzy==0.5.0"
    ],
    license="Creative Commons Attribution-NonCommercial 4.0 International License",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    include_package_data=True
)
