#!/usr/bin/env python

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

BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE = 30, 31, 32, 33, 34, 35, 36, 37
def cprint(string, color_code=30):
	print(f"\033[{color_code}m{string}\033[0m")

def wget(url:str, output_filename:str=None, output_dir:str=None, show_progress:bool=True, quiet:bool=True, auth:tuple[str, str]=None, headers:dict=None, print_cmd:bool=False):
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

def load_json_with_comments(content, encoding='utf-8'):
	if not type(content) is str:
		content = content.decode(encoding)
	r = ''
	i = 0
	while i < len(content)-1:
		if content[i]+content[i+1] == '/*':
			while content[i]+content[i+1] != '*/':
				i += 1
			i += 2

		if content[i]+content[i+1] == '//':
			while content[i] != '\n':
				i += 1
		r += content[i]
		i += 1
	r += content[i]
	return json.loads(r)

# init

class SDSetup:
	# constants
	config_filename = 'config.json'
	cache_filename = '.setup-cache'

	# defined at runtime
	wd = ''
	running_in_runpod_env = False
	models_folder = {}
	cache = {}
	args = []

	def load_config(self):
		if os.path.exists(self.config_filename):
			with open(self.config_filename, 'rb') as f:
				content = f.read()
				if content != b'':
					self.config = load_json_with_comments(content.decode('utf-8'))
				else:
					cprint(self.config_filename+' content is empty', RED)
					exit(1)
		else:
			cprint(f'Did not find {self.config_filename}', RED)
			exit(1)

	def load_cache(self):
		self.cache = {'updated-sd-repo': False, 'downloaded_models_in_discord_channel': [], 'models_in_civitai_favorites': []}
		if os.path.exists():
			with open(self.cache_filename, 'rb') as f:
				content = f.read()
				if content != b'':
					try:
						self.cache = json.loads(content.decode('utf-8'))
					except:
						cprint(f'failed to load {self.cache_filename}', RED)
						exit(1)
		self.cache['updated-sd-repo'] = self.config['skip_update_sd_repo']

	def parse_args(self):
		args_info = [
			[self.config['SELF_DESTROY'], self.config['SELF_DESTROY_SHORT'][1:], self.config['SELF_DESTROY_LONG']],
			[self.config['QUICK'], self.config['QUICK_SHORT'][1:], self.config['QUICK_LONG']],
			[self.config['USE_CIVITAI_FAVORITES'], self.config['USE_CIVITAI_FAVORITES_SHORT'][1:], self.config['USE_CIVITAI_FAVORITES_LONG']],
			[self.config['MOUNT'], self.config['MOUNT_SHORT'][1:], self.config['MOUNT_LONG']],
		]

		is_long_arg = [False]*(len(sys.argv)-1)
		for i in range(1, len(sys.argv)):
			for arg in args_info:
				if sys.argv[i] == arg[2]:
					arg[0] = True
					is_long_arg[i-1] = True
					break
		for i in range(1, len(sys.argv)):
			if not is_long_arg[i-1]:
				for arg in args_info:
					if arg[1] in sys.argv[i]:
						arg[0] = True

		self.args = [args_info[i][0] for i in range(len(args_info))]

	def clone_required_repos(self):
		# folders safety
		for folder in ['models', 'extensions', 'embeddings', 'repositories', 'models/Stable-diffusion', 'models/Lora', 'models/LyCORIS']:
			if not os.path.exists(folder):
				os.system('mkdir '+folder)

		# clone the lyoris repo
		if not os.path.exists('extensions/a1111-sd-webui-lycoris'):
			cprint('\ncloning the lycoris ripo...', GREEN)
			os.system('cd extensions && git clone https://github.com/KohakuBlueleaf/a1111-sd-webui-lycoris')
		
		# clone the stablediffusion 2.1 repo
		if not bool(self.cache['updated-sd-repo']):
			cprint('\ncloning the stablediffusion ripo...', GREEN)
			if os.path.exists('repositories/stable-diffusion-stability-ai'):
				os.system('rm -rf repositories/stable-diffusion-stability-ai')
			os.system('cd repositories && git clone https://github.com/Stability-AI/stablediffusion')
			os.system('mv repositories/stablediffusion repositories/stable-diffusion-stability-ai')
			self.cache['updated-sd-repo'] = True

	def __init__(self):
		self.load_config()
		self.parse_args()
		
		if self.args[3]:
			# mount the config.json file
			with open(__file__, 'rb') as f:
				content = f.read().decode('utf-8')
			mount = f'class SDSetup:\n\t'
			for key, value in self.config.items():
				if key == 'mounting_separator' and value == None: break
				if type(value) is str: value = f"'{value}'"
				mount += f'{key} = {value}\n\t'

			i = content.find('class SDSetup:')+len('class SDSetup:')
			j = content.find('# constants')-1
			content = content[:i]+'\n'+content[j:]
			content = content.replace('class SDSetup:', mount, 1)
			with open(__file__, 'w') as f:
				f.write(content)
				exit(0)
		else:
			# proceed with the initialization setup
			self.load_cache()
			self.wd = os.getcwd()
			self.running_in_runpod_env = wd == '/workspace/stable-diffusion-webui'
			self.discord_headers = {
				"authorization": self.config['discord_auth_token']
			}
			self.models_folder =  {
				"Checkpoint": f"{wd}/models/Stable-diffusion",
				"LORA": f"{wd}/models/Lora",
				"LoCon": f"{wd}/models/LyCORIS",
				"TextualInversion": f"{wd}/embeddings"
			}
			
			self.clone_required_repos()

	def get_messages(self):
		# get messages from channel
		cprint('getting messages...', BLUE)
		url = f"https://discord.com/api/v9/channels/{self.config['channel_id']}/messages?limit={self.config['msg_limit']}" if self.config['msg_limit'] != -1 else f"https://discord.com/api/v9/channels/{self.config['channel_id']}/messages"
		wget(url, output_filename='messages', headers=discord_headers)
		with open('messages', 'rb') as f:
			messages = json.loads(f.read().decode('utf-8'))
		

'''
try:

	
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
'''

def main():
	sdsetup = SDSetup()
	os.system("clear")
	# ...
	

if __name__ == '__main__':
	main()