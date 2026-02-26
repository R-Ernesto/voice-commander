from setuptools import setup, find_packages

setup(
    name="voice-commander",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "faster-whisper>=1.1.0",
        "sounddevice>=0.5.0",
        "numpy>=1.24",
        "keyboard>=0.13.5",
        "requests>=2.31",
        "pyperclip>=1.9",
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "voice-commander=voice_commander.main:main",
        ],
    },
    python_requires=">=3.10",
)
