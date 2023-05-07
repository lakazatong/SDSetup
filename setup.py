#!/usr/bin/env python

#------------------------------------------------------------------------------------------

# USER DEFINED VARIABLES

# always required
discord_auth_token = 'YOUR_TOKEN'

# required if you wish to use the --favorites argument
civitai_api_key = 'YOUR_API_KEY'
	
# self explanatory
server_id = 0
channel_id = 0
msg_limit = 50
show_files_progress_bar = False
show_models_progress_bar = True

# for debugging in local, should be False
# (IT ALLOWS FOR NSFW RESULTS, it will use the stable diffusion repo, not the one provided by runpod)
# (I also have to run the webui with the '--no-half-vae --precision full' args to never get black images it seems)
# (if anyone know why it creates black images when doing nsfw prompts in runpod, mp me at lakazatong#0206)
# (that would not need to clone the entire repo to speed up the setup)
skip_update_sd_repo = False 	

# default command line args

# example command :
# python setup.py -dqf
# it will :
# run the setup, destroy the setup.py, don't prompt Press Enter at the end and look at your civitai favorites as well

# destroy this script when it is done
SELF_DESTROY = False
SELF_DESTROY_SHORT = '-d'
SELF_DESTROY_LONG = '--destroy'
	
# skip the "Press Enter" when it is done
QUICK = False
QUICK_SHORT = '-q'
QUICK_LONG = '--quick'
	
# also look at models in your civitai favorites (REQUIRES YOUR CIVITAI API KEY)
USE_CIVITAI_FAVORITES = False
USE_CIVITAI_FAVORITES_SHORT = '-f'
USE_CIVITAI_FAVORITES_LONG = '--favorites'

# could seek for models and update the cache accordingly, but is not interesting to do as mentioned in the comments at the top of this file
# meaning right now it can say 'model_name is already deleted' but it is not because you installed it manually
# SEEK_FOR_MODELS = False
# SEEK_FOR_MODELS_SHORT = '-c'
# SEEK_FOR_MODELS_LONG = '--cache'

#------------------------------------------------------------------------------------------
				
# imports

import os
import sys
import subprocess
import json
try:
	from parsel import Selector
except:
	os.system("pip install parsel")
	from parsel import Selector

# functions

# here only GREEN (print is expected) and RED (print is not expected) are used
BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE = 30, 31, 32, 33, 34, 35, 36, 37

def cprint(string, color_code=30):
	print(f"\033[{color_code}m{string}\033[0m")

def wget(url, output_filename:str=None, output_dir:str=None, show_progress:bool=True, quiet:bool=True, auth:tuple[str, str]=None, headers:dict=None, print_cmd:bool=False):
	output_opt = f'-O "{output_filename}"' if output_filename != None else ''
	progress_opt = '--show-progress' if show_progress else ''
	quiet_opt = '-q' if quiet else ''
	auth_opt = f'--user "{auth[0]}" --password "{auth[1]}"' if auth != None else ''
	header_opt = ' '.join([f'--header="{key}: {value}"' for key, value in headers.items()]) if headers != None else ''
	cmd = f'wget {quiet_opt} {progress_opt} {output_opt} {auth_opt} {header_opt} "{url}"'
	if print_cmd:
		if header_opt != '': header_opt = '--header=...'
		print(f'wget {quiet_opt} {progress_opt} {output_opt} {auth_opt} {header_opt} {url}')
	
	if output_dir != None:
		if os.path.exists(output_dir):
			os.system(f'cd {output_dir} && {cmd}')
		else:
			cprint(f'\ncould not wget "{url}" in "{output_dir}" because it does not exists', RED)
			return
	else:
		os.system(cmd)

	full_path = f'{output_dir}/{output_filename}' if output_dir != None else output_filename
	if os.path.exists(full_path):
		with open(full_path, 'rb') as f:
			if f.read() == b'':
				cprint(f'\nthis command:\n{cmd}\ndownloaded a file of 0 bytes', RED)
	else:
		cprint(f'\nthis command:\n{cmd}\nseemed to have failed', RED)

def get_path(name, directory=None):
	if directory == None: directory = os.getcwd()
	path = None
	for root, dirs, files in os.walk(directory):
		if name in files:
			path = os.path.join(root, name)
			break
	return path

def find_index(lst, key, value):
	filtered = [i for i, d in enumerate(lst) if d.get(key) == value]
	return filtered[0] if len(filtered) > 0 else -1

# init

wd = os.getcwd()
running_in_runpod_env = wd == '/workspace/stable-diffusion-webui'
cache = {}

# if running_in_runpod_env:
# 	if wd != "/workspace/stable-diffusion-webui":
# 		cprint(f"setup.py must be put in /workspace/stable-diffusion-webui", RED)
# 		exit(1)

discord_headers = {
	"authorization": discord_auth_token
}

models_folder = {
	'Checkpoint': f'{wd}/models/Stable-diffusion',
	'LORA': f'{wd}/models/Lora',
	'LoCon': f'{wd}/models/LyCORIS',
	'TextualInversion': f'{wd}/embeddings'
}

try:

	# parse args
	args = [[SELF_DESTROY_LONG, SELF_DESTROY_SHORT, SELF_DESTROY], [QUICK_LONG, QUICK_SHORT, QUICK], [USE_CIVITAI_FAVORITES_LONG, USE_CIVITAI_FAVORITES_SHORT, USE_CIVITAI_FAVORITES]]

	is_long_arg = [False]*(len(sys.argv)-1)
	for i in range(1, len(sys.argv)):
		sys_arg = sys.argv[i]
		for arg in args:
			if sys_arg == arg[0]:
				arg[2] = True
				is_long_arg[i-1] = True
				break
	for i in range(1, len(sys.argv)):
		if not is_long_arg[i-1]:
			sys_arg = sys.argv[i]
			for arg in args:
				if arg[1] in sys_arg:
					arg[2] = True

	SELF_DESTROY = args[0][2]
	QUICK = args[1][2]
	USE_CIVITAI_FAVORITES = args[2][2]

	# load cache
	if os.path.exists('.setup-cache'):
		with open('.setup-cache', 'rb') as f:
			content = f.read()
			if content != b'':
				cache = json.loads(content)
	else:
		cache = {'updated-sd-repo': False, 'downloaded_models_in_discord_channel': [], 'models_in_civitai_favorites': []}

	cache['updated-sd-repo'] = skip_update_sd_repo

	os.system("clear")
	# folders safety
	for folder in ['models', 'extensions', 'embeddings', 'repositories', 'models/Stable-diffusion', 'models/Lora', 'models/LyCORIS']:
		if not os.path.exists(folder):
			os.system('mkdir '+folder)
	
	# clone the lyoris repo
	if not os.path.exists('extensions/a1111-sd-webui-lycoris'):
		cprint('\ncloning the lycoris ripo...', GREEN)
		os.system('cd extensions && git clone https://github.com/KohakuBlueleaf/a1111-sd-webui-lycoris')
	
	# clone the stablediffusion 2.1 repo
	if not bool(cache['updated-sd-repo']):
		cprint('\ncloning the stablediffusion ripo...', GREEN)
		if os.path.exists('repositories/stable-diffusion-stability-ai'):
			os.system('rm -rf repositories/stable-diffusion-stability-ai')
		os.system('cd repositories && git clone https://github.com/Stability-AI/stablediffusion')
		os.system('mv repositories/stablediffusion repositories/stable-diffusion-stability-ai')
		cache['updated-sd-repo'] = True
	

	# get messages from channel
	cprint('getting messages...', BLUE)
	wget(f"https://discord.com/api/v9/channels/{channel_id}/messages?limit={msg_limit}", output_filename='messages', headers=discord_headers)
	with open('messages', 'rb') as f:
		messages = json.loads(f.read().decode('utf-8'))
	k, n = 0, len(messages)
	currently_found_models_page_ids = []

	# perform the requested actions
	for i in range(n):

		INSTALL, DELETE, SKIP = False, False, False
		k += 1
		# parse reactions (prioritizes SKIP over DELETE if both reaction are on)
		if 'reactions' in messages[i]:
			for reaction in messages[i]['reactions']:
				emoji = bytes(reaction['emoji']['name'], 'utf-8')
				if emoji == b'\xe2\x9d\x8c':
					SKIP = True
					break
				elif emoji == b'\xf0\x9f\x9a\xab':
					DELETE = True
		else:
			INSTALL = True
				
		if SKIP:
			# file(s) to skip
			if messages[i]['attachments'] != []:
				for j in range(len(messages[i]['attachments'])):
					skipped_name = messages[i]['attachments'][j]['filename']
					cprint(f'\n({k}/{n})\nskipping {skipped_name}', GREEN)
			# model(s) to skip
			else:
				for j in range(len(messages[i]['embeds'])):
					title = messages[i]['embeds'][j]['title']
					skipped_name = title[:title.index('Stable Diffusion')-3].strip()
					cprint(f'\n({k}/{n})\nskipping {skipped_name}', GREEN)
		elif INSTALL:
			# file(s) to transfer
			if messages[i]['attachments'] != []:
				for j in range(len(messages[i]['attachments'])):
					file_url = messages[i]['attachments'][j]['url']
					file_name = messages[i]['attachments'][j]['filename'].strip()
					dir_path = wd
					# search for file (supposing there could be only one with this name)
					full_path = get_path(file_name)
					cprint(f'\n({k}/{n})', GREEN)
					# no file with name file_name found
					if full_path == None:
						# create it in wd by default
						full_path = f'{dir_path}/{file_name}'
						if not show_files_progress_bar: cprint(f'downloading {file_name} in {dir_path}...', GREEN)
					else:
						# overwrite the file found
						dir_path = os.path.dirname(full_path)
						if not show_files_progress_bar: cprint(f'overwriting {file_name} in {dir_path}...', GREEN)


					# # check if file was already downloaded
					# file_index = find_index(cache['files'], 'full_path', full_path)
					# # update cache, file might have moved over time
					# if file_index != -1: cache['files'].pop(file_index)
					# cache['files'].append( {'full_path': full_path, 'file_name': file_name, 'dir_path': dir_path} )


					wget(file_url, output_filename=file_name, output_dir=dir_path, show_progress=show_files_progress_bar)
			
			# model(s) to transfer
			else:
				for j in range(len(messages[i]['embeds'])):
					model_page_url = messages[i]['embeds'][j]['url']

					# check if model page is cached
					model_index = find_index(cache['downloaded_models_in_discord_channel'], 'model_page_url', model_page_url)
					if model_index == -1: model_index = find_index(cache['models_in_civitai_favorites'], 'model_page_url', model_page_url)


					cprint(f'\n({k}/{n})', GREEN)
					# no it is not
					if model_index == -1:
						# get its page
						wget(model_page_url, output_filename='page', show_progress=False)
						# parse the page
						with open('page', 'rb') as f:
							page = Selector(f.read().decode('utf-8'))
						# get its info
						model_info = json.loads(page.xpath('/html/body/script[1]/text()').get())['props']['pageProps']['trpcState']['json']['queries']
						model_type = str(model_info[1]['state']['data']['type']).strip()
						if model_type in models_folder:
							dir_path = models_folder[model_type]
						else:
							cprint(f'type "{model_type}" is not yet supported', RED)
							continue
						model_id = str(model_info[1]['state']['data']['modelVersions'][0]['id'])
						model_name = str(model_info[1]['state']['data']['name']).strip()
						model_url = 'https://civitai.com/api/download/models/'+model_id
						model_page_id = str(model_info[1]['state']['data']['modelVersions'][0]['modelId'])
						model_file_name = str(model_info[1]['state']['data']['modelVersions'][0]['files'][0]['name']).strip()
						# add it to cache
						cache['downloaded_models_in_discord_channel'].append({'model_type': model_type, 'model_id': model_id, 'model_name': model_name, 'model_url': model_url, 'model_page_id': model_page_id, 'model_file_name': model_file_name,  'model_page_url': model_page_url})
						full_path = f'{dir_path}/{model_file_name}'
						if os.path.exists(full_path):
							# was downloaded without the help of this script
							cprint(f'{model_name} is already installed', GREEN)
						else:
							# download it
							if not show_models_progress_bar: cprint(f'installing {model_name}...', GREEN)
							wget(model_url, output_dir=dir_path, output_filename=model_file_name, show_progress=show_models_progress_bar)
					# yes it is
					else:
						# get its info
						# model_type, model_id, model_name, model_url, model_page_id, model_file_name, model_page_url = cache['downloaded_models_in_discord_channel'][model_index].values()
						_, _, model_name, _, model_page_id, _, _ = cache['downloaded_models_in_discord_channel'][model_index].values()
						cprint(f'{model_name} is already installed', GREEN)

					currently_found_models_page_ids.append(model_page_id)
						
		elif DELETE:
			
			# file.s to delete
			if messages[i]['attachments'] != []:
				for j in range(len(messages[i]['attachments'])):
					# file_url = messages[i]['attachments'][j]['url']
					file_name = messages[i]['attachments'][j]['filename'].strip()
					dir_path = wd
					# search for file
					full_path = get_path(file_name)
					if full_path == None:
						full_path = f'{dir_path}/{file_name}'
					else:
						dir_path = os.path.dirname(full_path)
					cprint(f'\n({k}/{n})', GREEN)
					# delete the file
					if os.path.exists(full_path):
						cprint(f'deleting {full_path}...', GREEN)
						os.system(f'rm -f {full_path}')
					# file not found or was already deleted
					else:
						cprint(f'{full_path} is already deleted', GREEN)
					
					# # update cache
					# file_index = find_index(cache['files'], 'full_path', full_path)
					# # remove it from cache
					# if file_index != -1:
					# 	cache['files'].pop(file_index)
			
			# model.s to delete
			else:
				for j in range(len(messages[i]['embeds'])):
					model_page_url = messages[i]['embeds'][j]['url']

					# check if model page is cached
					model_index = find_index(cache['downloaded_models_in_discord_channel'], 'model_page_url', model_page_url)
					if model_index == -1: model_index = find_index(cache['models_in_civitai_favorites'], 'model_page_url', model_page_url)

					cprint(f'\n({k}/{n})', GREEN)
					# no it is not
					if model_index == -1:
						title = messages[i]['embeds'][j]['title']
						model_name = title[:title.index('Stable Diffusion')-3].strip()
						cprint(f'{model_name} is already deleted', GREEN)
					# yes it is
					else:
						# get its info
						model_type, _, model_name, _, _, model_file_name, _ = cache['downloaded_models_in_discord_channel'][model_index].values()
						dir_path = models_folder[model_type]
						full_path = f'{dir_path}/{model_file_name}'
						if os.path.exists(full_path):
							# delete it
							cprint(f'deleting {model_name}...', GREEN)
							os.system(f'rm -f {full_path}')
						else:
							# was deleted without the help of this script
							cprint(f'{model_name} is already deleted', GREEN)
						# remove it from cache
						cache['downloaded_models_in_discord_channel'].pop(model_index)


		else:
			cprint("\n???", RED)

	# delete models that are no longer in the discord channel
	for model in cache['downloaded_models_in_discord_channel']:
		if not model['model_page_id'] in currently_found_models_page_ids:
			k += 1
			cprint(f'\n({k}/{n})', GREEN)
			# user removed this model from the discord channel, interprets it as 'delete it'
			model_type = model['model_type']
			model_name = model['model_name']
			model_file_name = model['model_file_name']
			dir_path = models_folder[model_type]
			full_path = f'{dir_path}/{model_file_name}'
			if os.path.exists(full_path):
				cprint(f'deleting {model_name}...', GREEN)
				os.system('rm -f '+full_path)
				# updating cache (cannot use indices since we are iterating over the list itself :c)
				cache['models_in_civitai_favorites'].remove(model)
			else:
				cprint(f'{model_name} is already deleted', GREEN)

	if USE_CIVITAI_FAVORITES:

		cprint('\ngetting favorites...', BLUE)
		wget(f'https://civitai.com/api/v1/models?favorites=true&token={civitai_api_key}', output_filename='favorites')
		with open('favorites', 'rb') as f:
			favorites = json.loads(f.read().decode('utf-8'))

		k, n = 0, favorites['metadata']['totalItems']
		favorites = favorites['items']
		for model in favorites:
			k += 1
			cprint(f'\n({k}/{n})', GREEN)
			model_type = model['type']
			if model_type in models_folder:
				dir_path = models_folder[model_type]
			else:
				cprint(f'type "{model_type}" is not yet supported', RED)
				continue
			# check if model page is cached
			model_page_id = str(model['modelVersions'][0]['modelId'])
			model_index = find_index(cache['models_in_civitai_favorites'], 'model_page_id', model_page_id)
			if model_index == -1: model_index = find_index(cache['downloaded_models_in_discord_channel'], 'model_page_id', model_page_id)
			model_name = model['name']

			# no it is not
			if model_index == -1:
				# get its info
				model_id = str(model['modelVersions'][0]['id'])
				model_url = 'https://civitai.com/api/download/models/'+model_id
				model_file_name = model['modelVersions'][0]['files'][0]['name']
				model_page_url = f'https://civitai.com/models/'+model_page_id
				# add it to cache
				cache['models_in_civitai_favorites'].append({'model_type': model_type, 'model_id': model_id, 'model_name': model_name, 'model_url': model_url, 'model_page_id': model_page_id, 'model_file_name': model_file_name,  'model_page_url': model_page_url})
				# download it
				if not show_models_progress_bar: cprint(f'installing {model_name}...', GREEN)
				wget(model_url, output_dir=dir_path, output_filename=model_file_name, show_progress=show_models_progress_bar)
			# yes it is
			else:
				cprint(f'{model_name} is already installed', GREEN)
			
			currently_found_models_page_ids.append(model_page_id)
		
		# delete models that are no longer in civitai favorites
		for model in cache['models_in_civitai_favorites']:
			if not model['model_page_id'] in currently_found_models_page_ids:
				k += 1
				cprint(f'\n({k}/{n})', GREEN)
				# user removed this model from its favorites, interprets it as 'delete it'
				model_type = model['model_type']
				model_name = model['model_name']
				model_file_name = model['model_file_name']
				dir_path = models_folder[model_type]
				full_path = f'{dir_path}/{model_file_name}'
				if os.path.exists(full_path):
					cprint(f'deleting {model_name}...', GREEN)
					os.system('rm -f '+full_path)
					# updating cache (cannot use indices since we are iterating over the list itself :c)
					cache['models_in_civitai_favorites'].remove(model)
				else:
					cprint(f'{model_name} is already deleted', GREEN)

	# save cache
	with open('.setup-cache', 'w+') as f:
		json.dump(cache, f, indent=3)
	# for convenience
	# bashrc_path = '/root/.bashrc' if running_in_runpod_env else '~/.bashrc'
	bashrc_path = '/root/.bashrc' if running_in_runpod_env else get_path('.bashrc', directory='/')
	if bashrc_path != None:
		with open(bashrc_path, 'r') as f:
			bashrc_content = f.read()
		# bashrc_content = subprocess.check_output("cat ~/.bashrc", shell=True).decode('utf-8')
		if bashrc_content[-(len('alias r="python relauncher.py"')+1):].strip() != 'alias r="python relauncher.py"':
			os.system(f"echo 'alias r=\"python relauncher.py\"' >> {bashrc_path}")
		# done
		cprint('\nrun the r command to run the relauncher.py script', PURPLE)
	else:
		cprint('\ncould not find the .bashrc file', RED)
	cprint('\nAll done', BLUE)
	if not QUICK: os.system('bash -c "read -p \'\nPress Enter\'"')
	os.system("clear")
	# cleanup
	os.system(f'rm -f messages page favorites')
	# self destroys
	if SELF_DESTROY: subprocess.Popen('rm setup.py', shell=True)
	# reload terminal (to reload ~/.bashrc)
	os.system("exec bash")

except Exception as e:
	os.system(f'rm -f messages page favorites')
	os.system(f"echo {e}")
t_dir=dir_path, output_filename=model_file_name, show_progress=show_models_progress_bar)
			# yes it is
			else:
				cprint(f'{model_name} is already installed', GREEN)
			
			currently_found_models_page_ids.append(model_page_id)
		
		# delete models that are no longer in civitai favorites
		for model in cache['models_in_civitai_favorites']:
			if not model['model_page_id'] in currently_found_models_page_ids:
				k += 1
				cprint(f'\n({k}/{n})', GREEN)
				# user removed this model from its favorites, interprets it as 'delete it'
				model_type = model['model_type']
				model_name = model['model_name']
				model_file_name = model['model_file_name']
				dir_path = models_folder[model_type]
				full_path = f'{dir_path}/{model_file_name}'
				if os.path.exists(full_path):
					cprint(f'deleting {model_name}...', GREEN)
					os.system('rm -f '+full_path)
					# updating cache (cannot use indices since we are iterating over the list itself :c)
					cache['models_in_civitai_favorites'].remove(model)
				else:
					cprint(f'{model_name} is already deleted', GREEN)

	# save cache
	with open('.setup-cache', 'w+') as f:
		json.dump(cache, f, indent=3)
	# for convenience
	if running_in_runpod_env:
		with open('~/.bashrc', 'r') as f:
			bashrc_content = f.read()
		bashrc_content = subprocess.check_output("cat ~/.bashrc", shell=True).decode('utf-8')
		if bashrc_content[-(len('alias r="python relauncher.py"')+1):].strip() != 'alias r="python relauncher.py"':
			os.system("echo 'alias r=\"python relauncher.py\"' >> ~/.bashrc")
	# done
	cprint('\nAll done, run the r command to run the relauncher.py script', BLUE)
	if not QUICK: os.system('bash -c "read -p \'\nPress Enter\'"')
	os.system("clear")
	# cleanup
	os.system(f'rm -f messages page favorites')
	# self destroys
	if SELF_DESTROY: subprocess.Popen('rm setup.py', shell=True)
	# reload terminal (to reload ~/.bashrc)
	os.system("exec bash")

except Exception as e:
	os.system(f'rm -f messages page favorites')
	os.system(f"echo {e}")
	os.system(f"echo {e}")