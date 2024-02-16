from logging import getLogger
logger = getLogger('PyCriUsm.Key')


def _load_keys():
	import json
	from pathlib import Path
	with (Path(__file__).parent / 'keys.json').open('rb') as f:
		return json.load(f)


def _flat_key_map(keys):
	def core(data, share_dict: dict):
		i = None
		for i in data.values():
			break
		if isinstance(i, int):
			share_dict.update(data)
		elif isinstance(i, dict):
			for i in data.values():
				core(i, share_dict)
		else:
			raise TypeError('wrong keymap format')
		return share_dict

	def start_core(data):
		maps = {}
		core(data, maps)
		return maps

	from collections import defaultdict
	cache_map = defaultdict(dict)
	for i in keys.values():
		cache_map[i['Encrytion']].update(start_core(i['KeyMap']))
	return cache_map


raw_keys = _load_keys()
fast_lookup_keys = _flat_key_map(raw_keys)


def get_crypt_args_from_config(key, mode):
	hca_key = 0
	audio_encryption = bool(mode)
	if mode == 2:
		if hasattr(key, '__len__'):
			hca_key = key[1]
			key = key[0]
		else:
			hca_key = key
	return key, audio_encryption, hca_key


def get_key(video_path):
	key = 0
	mode = 0
	for mode, key_map in fast_lookup_keys.items():
		key = key_map.get(video_path.stem, 0)
		if key:
			break
	if key == 0:
		mode = 0
	return get_crypt_args_from_config(key, mode)