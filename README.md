# ossf-sast-ml

This repository contains an ML based code analyser for Static Application Security Testing (SAST) as part of [the extended version of Open Source Security Foundation (OSSF) project](https://github.com/viszkoktamas/ossf-cve-benchmark)

## Usage

### Prerequisites

- Python 3.8.10 (newer versions might not work with the required dependency versions)
- Node.js 20.18 (LTS)

### Installation

1. Clone the repository
2. Install the required Python packages globally (without venv) by running `pip install -r inference\requirements.txt`
3. Install the required Node.js packages by running `npm install` in the root directory

### Running the tool

Run the tool by running this command in the root directory:
```
$ node tool.js <path to the directory or list of files to analyze>
```

## Use your own models

If you want to use your own models, you can implement your own `prediction.py` file in the `inference` folder.
Your solution should implement the `predict` method imported in `inference/inference.py`.

For reference, you can check the branch named `feature/your-own-model` which showcases the implementation of a new model.

## Components of the tool

This tool consist of two components:
- **Linter**: This part is written in Node.js and is responsible for parsing the code, extracting every function as a separate instance and passing it to the Python part, which runs the inference.
  - **my-tool.js**: This is the main entry point of the tool. It handles errors and starts the execution of the tool.
  - **cli.js**: This file contains the logic for parsing the command line arguments and passing it to the code.
  - **lint.js**: This file contains the logic for parsing the code, extracting functions, saving it to a json file and running the Python part of the tool.
- **Inference**: This is the component that runs the inference on the code. It is responsible for loading the code, running the inference, and generating the alerts.
    - **inference.py**: This file contains the logic for running the inference. It loads the output of the linter to pass each function one by one to prediction.py, using the prediction's output it generates the alerts and saves it to the result json file.
    - **prediction.py**: This file contains the logic for running the prediction. It loads the model, runs the prediction, and returns it's result to the inference.py.
    - **requirements.txt**: This file contains the required Python packages for running the inference.

