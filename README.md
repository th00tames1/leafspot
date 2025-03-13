<img src="logo/main_icon.png" alt="icon" title="icon" width="200px" length="200px" />

## Septoria Leaf Spot Detector (SLSD)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Multi OS Test](https://github.com/th00tames1/leafspot/actions/workflows/MultiOS%20Test.yml/badge.svg)](https://github.com/th00tames1/leafspot/actions/workflows/MultiOS%20Test.yml)
## Introduction

Welcome to **SLSD**! This project is designed to detect the necrotic area on the black cottonwood leaf.

## Key Features

- **User-Friendly Interface:** Provides an intuitive GUI, easy-to-use.
- **Batch Processing Capability:** Detects multiple images at once. Just select multiple images or folder.
- **Time-Effective:** It can detect +1,000 images within an hour.
- **Comprehensive Reporting & Customization:** Automatically annotates images, generates detailed CSV reports.


## Installation

If using Anaconda 3, create a clean environment and activate it.  
In Anaconda Prompt, type the following these steps to install the project:
```bash
# Create Conda Environment
conda create -n YOUR_ENVIRONMENT_NAME python==3.10

# Activate Conda Environment
conda activate YOUR_ENVIRONMENT_NAME

# Install the PyPI & git (if there's an error about package dependencies)
conda install pip
conda install git

# Clone the repository
git clone https://github.com/th00tames1/leafspot.git

# Navigate to the project directory
cd leafspot

# Install dependencies
pip install -r requirements.txt
```

## How To Use

It's easy to run!
```bash
python run.py
```
GUI software will appear soon. It may take up to about one minute on the first run.

![SW Thumbnail](logo/Thumbnail.png "Thumbnail")

1. Open Images by click 'Open File' or 'Open Folder'.  
The example images are located in the **'test_images folder'**. Or, you can download by use this google drive link: https://drive.google.com/drive/folders/10MSsa04RvnxVbzmnlWHY5Ggod6un33EV?usp=sharing

2. Click 'Run'.

3. The prediction result images and .csv reports will be saved.


## License

Copyright Heechan Jeong (Advanced Forestry Systems Lab, OSU), 2025.

Distributed under the terms of the MIT license, Leaf Spot Detector is free and open source software.
