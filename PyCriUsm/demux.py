from io import FileIO, BytesIO
from logging import getLogger
from pathlib import Path
from queue import SimpleQueue
from struct import Struct
from typing import Union

from .fast_core import UsmCrypter, HcaCrypter, FastUsmFile
from .key import get_key
from .util import reg_dict, io_pool, cpu_pool

logger = getLogger('PyCriUsm.Demuxer')
_usm_header_struct = Struct(r'>4sLxBHBxxBLL8x')
crypt_cache = ({}, {})


def get_crypter(key, is_hca=False):
	return reg_dict(crypt_cache[is_hca], key, lambda: (UsmCrypter, HcaCrypter)[is_hca](key))


def cleanup_cryptor():
	crypt_cache[0].clear()
	crypt_cache[1].clear()


def extract_usm(video_path, output, is_async: bool, **kwargs):
	video_path = Path(video_path)
	key_args = get_key(video_path)
	return demux(video_path, output, *key_args, is_async, **kwargs)


def _decrypt_usm(usm_decrypter: UsmCrypter, hca_decrypter, input_queue: SimpleQueue, output_queue: SimpleQueue):
	video_decrypt = usm_decrypter.decrypt_video if usm_decrypter else None
	audio_decrypt = hca_decrypter.decrypt if hca_decrypter else usm_decrypter.crypt_audio if usm_decrypter else None
	while True:
		buffer = input_queue.get()
		if buffer is None:
			break
		if buffer.is_video:
			if video_decrypt:
				video_decrypt(buffer)
		else:
			if audio_decrypt:
				audio_decrypt(buffer)
		output_queue.put(buffer)


def demux(video_path, output: Union[str, Path, SimpleQueue], key=0, audio_encrypt=False, hca_encrypt=0,
		  is_async=False, filter_mode=0, audio_chno=(), video_chno=()):
	"""
	:param video_path: same meaning as arg name
	:param output: path-like object or queue.Queue
	:param key: usm decryption key, 0 means no encryption
	:param audio_encrypt: enable usm audio decryption
	:param hca_encrypt: 0 not provided, 1 same key as usm, other custom key
	:param filter_mode: param to FastUsmFile
	:param audio_chno: param to FastUsmFile
	:param video_chno: param to FastUsmFile
	:return: a coro or the result
	"""
	def write_loop(queue: SimpleQueue, output):
		def write_cache(cache, data):
			buffer = reg_dict(cache, data.chno, BytesIO)
			write_file(buffer, data)

		def write_file_from_cache(cache, suffix):
			ret = {}
			for inno, buffer in cache.items():
				file_name = output / f'{video_path.stem}_{inno}{suffix}'
				ret[inno] = file_name
				with FileIO(file_name, 'wb') as f:
					f.write(buffer.getbuffer())
			return ret

		def write_file(fobj, data):
			nonlocal finish_flag
			index = data.index
			if index == chunk_cache[0]:
				fobj.write(data)
				new_index = index + 1
				while True:
					data = chunk_cache[1].pop(new_index, None)
					if data is None:
						break
					fobj.write(data)
					new_index += 1
				chunk_cache[0] = new_index
				if max_index is not None:
					if new_index == max_index:
						if chunk_cache[1]:
							breakpoint()
						else:
							finish_flag = True
					elif new_index > max_index:
						print('逻辑有问题')
						breakpoint()
			elif index > chunk_cache[0]:
				chunk_cache[1][index] = data
			else:
				raise ValueError('写入排序逻辑有问题')
			for i in chunk_cache[1]:
				if i < chunk_cache[0]:
					breakpoint()

		logger = getLogger('PyCriUsm.writer')
		logger.debug(r'进入成功')
		memory_cache = ({}, {})
		chunk_cache = [0, {}]
		stream_video_path = None
		stream_video = None
		max_index = None
		finish_flag = False
		# await write_lock.acquire(1)
		while True:
			data = queue.get(timeout=1)
			# check
			if isinstance(data, int):
				if data == chunk_cache[0]:
					break
				elif data < chunk_cache[0]:
					print('逻辑有问题')
					breakpoint()
				max_index = data
				continue
			if data.is_video and data.chno == 0:
				if stream_video_path is None:
						stream_video_path = output / (video_path.stem + '.ivf')
						stream_video = stream_video_path.open('wb')
				write_file(stream_video, data)
			else:
				write_cache(memory_cache[data.is_video], data)
			del data
			if finish_flag:
				break

		print(f'写入{video_path}完成')
		# check logic
		for b in chunk_cache[1].values():
			if b[1]:
				breakpoint()

		# write cache to file
		if stream_video:
			stream_video.close()
		logger.debug('开始写入音频')
		audios = write_file_from_cache(memory_cache[0], '.adx')
		videos = write_file_from_cache(memory_cache[1], '.ivf')
		videos[0] = stream_video_path
		return videos, audios

	def read_loop():
		buffer = None
		threads = ()
		input_queue = SimpleQueue() if key else None
		video_call = input_queue.put if key else output_queue.put
		# TODO hca decrypt support
		audio_call = input_queue.put if audio_encrypt and hca_encrypt==0 else output_queue.put
		if key:
			threads = tuple(cpu_pool.submit(_decrypt_usm, usm_decrypter, None, input_queue, output_queue) for _ in range(3))

		if id(video_call) == id(audio_call):
			for buffer in usm_file.iter_chunks(filter_mode, audio_chno, video_chno):
				video_call(buffer)
		else:
			for buffer in usm_file.iter_chunks(filter_mode, audio_chno, video_chno):
				if buffer.is_video:
					video_call(buffer)
				else:
					audio_call(buffer)

		if buffer:
			output_queue.put(buffer.index + 1)
		else:
			logger.debug('啥都没输出')
			output_queue.put(0)
		print(f'{video_path}读取完成')
		for i in range(len(threads)):
			input_queue.put(None)
		for i in threads:
			i.result()

	usm_file = FastUsmFile(video_path)
	video_path = Path(video_path)
	output_queue = SimpleQueue()
	usm_decrypter = None
	write_coro = None
	if key:
		usm_decrypter = get_crypter(key, bool(hca_encrypt))
	if is_async:
		async def wait():
			from .util import async_wait
			return (await async_wait(read_coro, write_coro))[1]
	else:
		def wait():
			from .util import coro_wait
			return coro_wait()[1]
	read_coro = io_pool.submit(read_loop)
	if isinstance(output, SimpleQueue) is False:
		output = Path(output)
		output.mkdir(parents=True, exist_ok=True)
		write_coro = io_pool.submit(write_loop, output_queue, output)
	return wait()
