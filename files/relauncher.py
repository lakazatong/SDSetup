import sys, os, time

if sys.platform.startswith('win'):
	launch_string = 'webui-user.bat'
else:
	launch_string = 'webui.sh -f'

n = 0
while True:
	os.system("clear")
	print('Relauncher: Launching...')
	if n > 0:
		print(f'\tRelaunch count: {n}')
	os.system(launch_string)
	print('Relauncher: Process is ending. Relaunching in 2s...')
	n += 1
	time.sleep(2)