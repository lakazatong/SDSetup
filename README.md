# SDSetup

Setup your Stable Diffusion web UI repository by looking at files and civitai model links sent in the Discord channel of you choice.
<!-- 
## Requirements

- A Stable Diffusion web UI repository (https://github.com/AUTOMATIC1111/stable-diffusion-webui)
- A Discord account (https://discord.com)
- A Civitai account (https://civitai.com) (optional) -->

## Installation and Running

Download the setup.py and config.json files or just run:
```
git clone https://github.com/lakazatong/SDSetup
```

Fill up config.json with the required fields and your preferences, then run:
```
python setup.py -m
```
Your setup.py is now ready!

Paste it in any Stable Diffusion web UI repository and run:
```
python setup.py
```
Your Stable Diffusion web UI repository is now setup!

## Instructions

- Use reactions to give instructions in the discord channel : ❌ SKIP, 🚫 DELETE.

## Warnings

- This script do not check if models were manually installed before the first setup, because models file names could have been renamed thus giving no information on what model it is. It could not even know if it's on civitai (a -c, --cache option could be added to seek for installed models and update cache with what it finds but sounds not reliable at all). So if you want all your previous models to be managed by this script as well, delete them all and let it download them setting up its cache.

- If you see (12/11) for example that means it is going through the cache and figuring out if some of the models were not found in the discord channel or your civitai favorites and deleting them if so.

- The only right way to reset the cache is to delete the .setup-cache cache file.

- Do not rename downloaded models, it can cause issues.

## TODO

- Add a prompt in case there are multiple files included with the model link (could also just be a VAE, in that case download it without prompting the user).

- Add a way to rename downloaded models without breaking everything lol (updating the cache basically, could be done with smth like python setup.py -r \<path to model\> new_name (with or without the extension, using the path to be able to use TAB so that it's easier).

- Add support for all other types (poses, controlnet, ...).

- Have a preferred sampling method for each checkpoint (guess it based on the one used in the previews and prompt the user or use a default one if no preview).

- Cache settings after each txt2img generation in case it crashes and load them after reloading.

- Install controlnet by default (poses by default or user defined? maybe).

- Add previews automatically.

- Close the runpod after ~5 mins and terminate it after ~10 mins of inactivity.