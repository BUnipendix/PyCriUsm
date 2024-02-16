from pathlib import Path
import json


def import_helper(path):
	from importlib.util import spec_from_file_location, module_from_spec
	path = path / "get_keys.py"
	if path.is_file() is False:
		return
	spec = spec_from_file_location("get_keys", str(path))
	if spec is None:
		Warning(f'Could not find {path.parent.name}\'s keygen module')
		return
	module = module_from_spec(spec)
	spec.loader.exec_module(module)
	return getattr(module, 'get_keys', None)


def main():
	keys = {}
	root = Path(__file__).parent
	for i in root.iterdir():
		if i.is_file():
			continue
		get_keys_func = import_helper(i)
		if get_keys_func is None:
			continue
		data = get_keys_func()
		keys[i.name] = {'Encrytion': data[0], 'KeyMap': data[1]}
	with open(root.parent / 'pycriusm/keys.json', 'w') as f:
		json.dump(keys, f, ensure_ascii=False, indent='\t')


if __name__ == '__main__':
	main()