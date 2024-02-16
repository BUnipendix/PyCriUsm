import asyncio
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from os import cpu_count as _cpu_count
cpu_pool = ThreadPoolExecutor()
io_pool = ThreadPoolExecutor(_cpu_count() * 2)


def init_log(name: str, is_debug=False):
	import logging
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG if is_debug else logging.INFO)

	console_handler = logging.StreamHandler()
	console_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)-4s: %(message)s')
	console_handler.setFormatter(console_formatter)
	logger.addHandler(console_handler)


async def async_wait(*futures: Future):
	loop = asyncio.get_running_loop()
	ret = []
	for future in futures:
		if isinstance(future, Future):
			future = await asyncio.wrap_future(future, loop=loop)
		ret.append(future)
	return ret


def coro_wait(*futures: Future):
	ret = []
	for future in futures:
		if isinstance(future, Future):
			future = future.result()
		ret.append(future)
	return ret


def reg_dict(dic: dict, key, init_factory):
	obj = dic.get(key, None)
	if obj is None:
		obj = init_factory()
		dic[key] = obj
	return obj
