# Leaf Spot Detector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Introduction

Welcome to **Leaf Spot Detector**! This project is designed to detect the necrotic area on the leaf.

## Key Features

- **User-Friendly Interface:** Provides an intuitive GUI for loading images or folders, and for viewing both original and prediction result images side by side.
- **Advanced YOLO-Based Detection:** Utilizes a YOLO model to accurately detect leaf and spot areas with adjustable thresholds for optimal performance.
- **Comprehensive Reporting & Customization:** Automatically annotates images, generates detailed CSV reports.
- **Batch Processing Capability:** Enables running detection on multiple images at once.

## Installation

If using Anaconda 3, create a clean environment and activate it. \n
In Anaconda Prompt, type the following these steps to install the project:
```bash
# Create Conda Environment
conda create -n YOUR_ENVIRONMENT_NAME python==3.10

# Activate Conda Environment
conda activate YOUR_ENVIRONMENT_NAME

# Install the PyPI & git (if there's an error)
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

It's easy to run! It may take up to about one minute on the first run.
```bash
python run.py
```

1. Open Images by click 'Open File' or 'Open Folder'. 
The example file is located in the test_images folder.

2. Click 'Run'.

3. The prediction result images and .csv reports will be saved.


## License

Copyright Heechan Jeong, 2025.

Distributed under the terms of the MIT license, Leaf Spot Detector is free and open source software.