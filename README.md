# SDSetup

Setup your Stable Diffusion web UI repository by looking at files and civitai model links sent in the Discord channel of you choice.

Disclaimer: for now I use this repo as a way to have it uploaded and online and keep track of the progress, commits are by no means "good commits".
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

* On Linux or WSL:

Paste it in any Stable Diffusion web UI repository and run:
```
python setup.py
```
Your Stable Diffusion web UI repository is now setup!

* On Windows:

Does not work on windows for now.

## Instructions and Tips

- Use reactions to give instructions in the discord channel : 🚫 SKIP, ❌ DELETE (prioritizes SKIP over DELETE if both reaction are on).

- Some good to have files are in the files folder, you can upload them in your Discord channel if you like.

Some interesting lines in ui-config.json (for A1111 release 1.5.2):

	txt2img:
	
		3: default positive prompt
		5: default negative prompt
		37: default sampling method
		39: default sampling steps
		83: default width
		88: default height
		94: default batch count
		99: default batch size
		104: default CFG scale
		109: default seed

	img2img:

		189: default positive prompt
		191: default negative prompt
		240: default resize mode
		262: default sampling method
		264: default sampling steps
		273: default width
		278: default height
		295: default batch count
		300: default batch size
		305: default CFG scale
		314: default denoising strength
		319: default seed

## Warnings

- This script do not check if models were manually installed before the first setup, because models file names could have been renamed thus giving no information on what model it is. It could not even know if it's on civitai (a -c, --cache option could be added to seek for installed models and update cache with what it finds but sounds not reliable at all). So if you want all your previous models to be managed by this script as well, delete them all and let it download them setting up its cache.

- If you see (12/11) for example that means it is going through the cache and figuring out if some of the models were not found in the discord channel or your civitai favorites and deleting them if so.

- The only right way to reset the cache is to delete the .setup-cache cache file.

- Do not rename downloaded models, it can cause issues.

## FAQ

- What's 'discord_auth_token' and how can I obtain mine?

Go to https://discord.com/app in your browser, login if not already, open the Developer Tools by pressing f12, go to the Network tab, make sure it is recording traffic by noticing:

on Chrome / Firefox

![Chrome](https://cdn.discordapp.com/attachments/859861167484174369/1106801770556039290/2023-05-13_06-33-23.png)
![Firefox](https://cdn.discordapp.com/attachments/859861167484174369/1106801770291806248/2023-05-13_06-32-33.png)

Click on any channel from any server, press ctrl+f, enter 'Authorization' in the Search field that opened on the left, you should get something like this:

![Search](https://cdn.discordapp.com/attachments/859861167484174369/1106803436885905419/image.png)

The 'discord_auth_token' you are looking for is in these files, if you click on one you will get redirected to the file, scroll down to Request Headers, it will be highlighted in yellow c:

- What's 'civitai_api_key' and how can I obtain mine?

Go to https://civitai.com/user/account, login, scroll down, in 'API Keys' click 'Add API key', enter the name you want and copy the key you got, that's it c:

- How can I get the ID of a Discord channel?

Right click on the channel and click 'Copy Channel ID' c:

## TODO

- Windows support

- Add a prompt in case there are multiple files included with the model link (could also just be a VAE, in that case download it without prompting the user).

- Add a way to rename downloaded models without breaking everything lol (updating the cache basically, could be done with smth like python setup.py -r \<path to model\> new_name (with or without the extension, using the path to be able to use TAB so that it's easier).

- Add support for all other types (poses, controlnet, ...).

- Have a preferred sampling method for each checkpoint (guess it based on the one used in the previews and prompt the user or use a default one if no preview).

- Cache settings after each txt2img generation in case it crashes and load them after reloading.

- Close the runpod after ~5 mins and terminate it after ~10 mins of inactivity.