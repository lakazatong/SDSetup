import sys, os, time

if sys.platform.startswith('win'):
	ext = 'bat'
else:
	ext = 'sh'

n = 0
while True:
	os.system("clear")
	print('Relauncher: Launching...')
	if n > 0:
		print(f'\tRelaunch count: {n}')
	launch_string = f'webui.{ext} -f'
	os.system(launch_string)
	print('Relauncher: Process is ending. Relaunching in 2s...')
	n += 1
	time.sleep(2)