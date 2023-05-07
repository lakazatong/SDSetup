# SDSetup

Setup your Stable diffusion repo (mainly for runpod rn)


# Instructions

- Use reactions to give instructions in the discord channel : None -> INSTALL, 🚫 (b'\xf0\x9f\x9a\xab') -> DELETE FILE, ❌ (b'\xe2\x9d\x8c') -> SKIP

- The only right way to reset the cache is to delete the .setup-cache cache file located where this file is

- Do not rename downloaded models, it can cause issues

# Warnings

- This script do not check if models were manually installed, because file names could have been renamed thus giving no information on what model it is

- It could not even know if it's on civitai (a -c | -cache option could be added to seek for installed models and update cache with what it finds but meh)

- So if you want all your models to be managed by this script... delete them all and let it download them setting up its cache... I know it's annoying

- If you see (12/11) for example that means it is going through the cache and figuring out if some of the models were not found in the discord channel or your civitai favorites and deleting them if so

# TODO

- Split up setup.py into files and factorize some of the code into classes and stuff

- Add a prompt in case there are multiple files included with the model link (could also just be a VAE, in that case download it without prompting the user)

- Add a way to rename downloaded models without breaking everything lol (updating the cache basically, could be done with smth like python setup.py -r \<path to model\> new_name (with or without the extension, using the path to be able to use TAB so that it's easier)

- Add support for all other types (poses, controlnet, ...)

- Have a preferred sampling method for each checkpoint (guess it based on the one used in the previews and prompt the user or use a default one if no preview)

- Cache settings after each txt2img generation in case it crashes and load them after reloading

- Install controlnet by default (poses by default or user defined? maybe)

- Add previews automatically

- Close the runpod after ~5 mins and terminate it after ~10 mins of inactivity
