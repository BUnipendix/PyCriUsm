import asyncio
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from os import cpu_count as _cpu_count
cpu_pool = ThreadPoolExecutor()
io_pool = ThreadPoolExecutor(_cpu_count() * 2)


async def async_wait(*futures: Future):
	loop = asyncio.get_running_loop()
	ret = []
	for future in futures:
		if isinstance(future, Future) and future.running():
			ret.append(await asyncio.wrap_future(future, loop=loop))
	return ret


def coro_wait(*futures: Future):
	ret = []
	for future in futures:
		if isinstance(future, Future) and future.running():
			ret.append(future.result())
	return ret


def reg_dict(dic: dict, key, init_factory):
	obj = dic.get(key, None)
	if obj is None:
		obj = init_factory()
		dic[key] = obj
	return obj
