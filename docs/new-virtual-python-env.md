# Setting Up a Python Virtual Environment

In this guide, we will cover how to create and activate a new Python virtual environment (venv) or a new conda environment.

## Python Virtual Environment (venv)

### Windows

1. Open a Command Prompt.

2. Navigate to your project directory using the `cd` command, e.g.:
```shell
cd C:\Users\username\project_directory


3. Run the following command to create a virtual environment named `venv`:
```shell
python -m venv venv
```

4. Activate the virtual environment using:
```shell
.\venv\Scripts\activate
```

### macOS and Linux

1. Open a Terminal.

2. Navigate to your project directory using the `cd` command, e.g.:
```shell
cd /Users/username/project_directory
```

3. Run the following command to create a virtual environment named `venv`:
```shell
python3 -m venv venv
```

4. Activate the virtual environment using:
```shell
source venv/bin/activate
```

## Conda Environment

1. Install [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) if you haven't already.

2. Open a Terminal or Anaconda Prompt.

3. Create a new conda environment by running the following command, replacing `env_name` with your desired environment name:
```shell
conda create --name env_name python=3.8
```

4. Activate the conda environment using:
```shell
conda activate env_name
```

Now you have successfully created and activated a new Python virtual environment (venv) or a new conda environment. Proceed with the next steps in the installation process.
