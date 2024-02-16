from dataclasses_json import dataclass_json, LetterCase
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class VideoConfigRow:
	video_id: int = 0
	video_path: str = ''
	is_player_involved: bool = False
	caption_path: str = ''
	encryption: bool = False


def _get_hsr_decrypt_key(video_name: str, version_key: int):
	video_name = video_name.encode()
	name_hash = 0
	for i in video_name:
		name_hash = (name_hash * 11 + i) & 0xffffffffffffffff
	return ((version_key + name_hash) & 0xffffffffffffffff) % 72043514036987937


def get_keys():
	root = Path(__file__).parent
	loaded_key = set()
	all_keys = {}
	for sub_root in root.iterdir():
		if sub_root.is_file() or sub_root.name[0].isdigit() is False:
			continue
		with open(sub_root / 'GetVideoVersionKeyScRsp.json') as f:
			data = tuple(json.load(f).values())
		data = data[0]
		tmp_keys = {}
		for i in data:
			key1, key2 = map(int, i.values())
			if key1 > 10000000:
				if key2 not in tmp_keys:
					tmp_keys[key2] = key1
			else:
				if key1 not in tmp_keys:
					tmp_keys[key1] = key2

		keys = {}
		with open(sub_root / 'VideoConfig.json') as f:
			data = json.load(f)
		if isinstance(data, dict):
			data = data.values()
		for i in data:
			i = VideoConfigRow.from_dict(i)
			if i.video_id in loaded_key:
				continue
			loaded_key.add(i.video_id)
			if i.encryption is False:
				continue
			version_key = tmp_keys.get(i.video_id, None)
			if version_key is None:
				Warning(f'Could not find {i.video_path} key')
				continue
			names = i.video_path.removesuffix('.usm')
			if i.is_player_involved:
				names = (names + '_f', names + '_m')
			else:
				names = (names,)
			for name in names:
				if name in keys:
					continue
				key = _get_hsr_decrypt_key(name, version_key)
				keys[name] = key
		all_keys[sub_root.name] = keys
	return 1, all_keys

