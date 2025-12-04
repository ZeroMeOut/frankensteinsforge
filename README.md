
# Frankenstein's Forge

If you stumbled upon this without knowing this was for a competition, hello :). This is basically an idea generator using text, images, and/or audio. What makes it a bit different from just using a multimodal model straight up is the ability to use weighted connection bewteen the nodes to influence the idea generation. You can watch a video of me doing a demo of it [here](https://youtu.be/dJtR7N6Fb_k?si=N_s8_DMUIvpasLWM). 

You can access it online with a website somewhere on this github, which may or may not be down if my budget allows it. If it is down you can just run it locally.



## Running Locally
First you will need an api key from [Google AI Studio](https://aistudio.google.com) and your quota tier needs to be tier 1 or higher for this to run without errors.  Also python and git installed on your computer if you haven't.

### Installation
First pip install uv
```bash
pip install uv 
```

Git clone this repo and enter into the folder
```bash
git clone https://github.com/ZeroMeOut/frankensteinsforge.git
cd frankensteinsforge
```

Create a virtual environment with python 3.11
```bash
uv venv --python 3.11
```

If you are using vscode or Kiro it should auto use your environment if you open an new terminal, else activate the environment
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install all the dependencies from the requirements.txt
```bash
uv pip install -r requirements.txt
```

Create a `.env` file and in there add this line
```env
GOOGLE_API_KEY=your_google_api_key_here
```

Finally run the `main.py` with `python main.py` and open `http://localhost:8000` in your brower :)

If you have any problems running it feel free to contact me on discord, zeromeout.

## Random Thoughts
This is the first time I am using Kiro to build something, it gets some getting use to tbh, especially if you don't use any steering docs. It's pretty good overall, should defo try it out if you haven't :). 

As for the project, it's just something that randomly hit me while I was on my bed. I think it could be somthing more but idk, I don't plan on touching it anymore cuz of personal stuff happening irl. Till next time.
## License

[MIT](https://choosealicense.com/licenses/mit/)

