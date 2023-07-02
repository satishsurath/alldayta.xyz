# alldayta.xyz
GPT based Virtual teaching assistant



## 💻 Installation

1. Create and activate a [new Python virtual environment (venv) or a new conda environment.](/docs/new-virtual-python-env.md)

   
2. Clone this repository:
   ```shell
   git clone git@github.com:satishsurath/alldayta.xyz.git
    ```

3. Set up your OpenAI API Key as an environment variable. [Request an API key here.](https://openai.com/blog/openai-api)
```shell
export OPENAI_API_KEY=[YOUR-OPENAI_API_KEY-HERE]
```

4. Install all Python dependencies in your environment:
```shell
pip install -r requirements.txt
```

5. Configure Authorized Logins by editing the ```app/settings/sample.users.json``` and renaming it to ```users.json```