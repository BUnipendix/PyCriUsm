from libc.string cimport memcpy
from cython cimport boundscheck, wraparound

cdef class VideoDecrypter:
	cdef unsigned char[0x20] _video_mask1
	cdef unsigned char[0x20] _video_mask2
	cdef unsigned char[0x20] _audio_mask

	def __init__(self, unsigned long int_key1, unsigned long int_key2):
		cdef unsigned char[4] key1 = <unsigned char*>&int_key1
		cdef unsigned char[4] key2 = <unsigned char*>&int_key2
		cdef unsigned char[4] table2 = [85, 82, 85, 67]
		cdef unsigned char* tmp_video_mask1 = self._video_mask1
		cdef unsigned char* tmp_video_mask2 = self._video_mask2
		cdef unsigned char* tmp_audio_mask = self._audio_mask
		cdef unsigned int i
		with nogil:
			tmp_video_mask1[0x00] = key1[0]
			tmp_video_mask1[0x01] = key1[1]
			tmp_video_mask1[0x02] = key1[2]
			tmp_video_mask1[0x03] = key1[3] - 0x34
			tmp_video_mask1[0x04] = key2[0] + 0xF9
			tmp_video_mask1[0x05] = key2[1] ^ 0x13
			tmp_video_mask1[0x06] = key2[2] + 0x61
			tmp_video_mask1[0x07] = tmp_video_mask1[0x00] ^ 0xFF
			tmp_video_mask1[0x08] = tmp_video_mask1[0x02] + tmp_video_mask1[0x01]
			tmp_video_mask1[0x09] = tmp_video_mask1[0x01] - tmp_video_mask1[0x07]
			tmp_video_mask1[0x0A] = tmp_video_mask1[0x02] ^ 0xFF
			tmp_video_mask1[0x0B] = tmp_video_mask1[0x01] ^ 0xFF
			tmp_video_mask1[0x0C] = tmp_video_mask1[0x0B] + tmp_video_mask1[0x09]
			tmp_video_mask1[0x0D] = tmp_video_mask1[0x08] - tmp_video_mask1[0x03]
			tmp_video_mask1[0x0E] = tmp_video_mask1[0x0D] ^ 0xFF
			tmp_video_mask1[0x0F] = tmp_video_mask1[0x0A] - tmp_video_mask1[0x0B]
			tmp_video_mask1[0x10] = tmp_video_mask1[0x08] - tmp_video_mask1[0x0F]
			tmp_video_mask1[0x11] = tmp_video_mask1[0x10] ^ tmp_video_mask1[0x07]
			tmp_video_mask1[0x12] = tmp_video_mask1[0x0F] ^ 0xFF
			tmp_video_mask1[0x13] = tmp_video_mask1[0x03] ^ 0x10
			tmp_video_mask1[0x14] = tmp_video_mask1[0x04] - 0x32
			tmp_video_mask1[0x15] = tmp_video_mask1[0x05] + 0xED
			tmp_video_mask1[0x16] = tmp_video_mask1[0x06] ^ 0xF3
			tmp_video_mask1[0x17] = tmp_video_mask1[0x13] - tmp_video_mask1[0x0F]
			tmp_video_mask1[0x18] = tmp_video_mask1[0x15] + tmp_video_mask1[0x07]
			tmp_video_mask1[0x19] = 0x21 - tmp_video_mask1[0x13]
			tmp_video_mask1[0x1A] = tmp_video_mask1[0x14] ^ tmp_video_mask1[0x17]
			tmp_video_mask1[0x1B] = tmp_video_mask1[0x16] + tmp_video_mask1[0x16]
			tmp_video_mask1[0x1C] = tmp_video_mask1[0x17] + 0x44
			tmp_video_mask1[0x1D] = tmp_video_mask1[0x03] + tmp_video_mask1[0x04]
			tmp_video_mask1[0x1E] = tmp_video_mask1[0x05] - tmp_video_mask1[0x16]
			tmp_video_mask1[0x1F] = tmp_video_mask1[0x1D] ^ tmp_video_mask1[0x13]

			for i in range(0x20):
				tmp_video_mask2[i] = tmp_video_mask1[i] ^ 0xFF
				tmp_audio_mask[i] = table2[i >> 1 & 3] if i & 1 == 1 else tmp_video_mask1[i] ^ 0xFF

	@wraparound(False)
	def decrypt_video(self, unsigned char* data, unsigned long long size):
		cdef unsigned long long i
		cdef unsigned long long dataOffset = 0x40
		cdef unsigned char[0x20] mask
		if size < 0x240:
			return
		size -= dataOffset
		with boundscheck(False):
			with nogil:
				memcpy(mask, self._video_mask2, sizeof(mask))
				for i in range(0x100, size):
					data[i + dataOffset] ^= mask[i & 0x1F]
					mask[i & 0x1F] = data[i + dataOffset] ^ self._video_mask2[i & 0x1F]
				memcpy(mask, self._video_mask1, sizeof(mask))
				for i in range(0x100):
					mask[i & 0x1F] ^= data[0x100 + i + dataOffset]
					data[i + dataOffset] ^= mask[i & 0x1F]
		return data[:size + dataOffset]

	@wraparound(False)
	def crypt_audio(self, unsigned char* data, unsigned long long size):
		cdef unsigned long long i
		if size <= 0x140:
			return
		with boundscheck(False):
			with nogil:
				for i in range(0x140, size):
					data[i] ^= self._audio_mask[i & 0x1f]
		return data[:size]


cdef unsigned char* init_default_audio_ciph(unsigned char* _ciphTable):
	cdef unsigned long long i
	cdef unsigned char v = 0
	for i in range(0xff):
		v = v * 13 + 11
		if v == 0 or v == 0xFF:
			v = v * 13 + 11
		_ciphTable[i] = v
	_ciphTable[0] = 0
	_ciphTable[0xFF] = 0xFF

cdef unsigned char[0x100] default_audio_ciph_table
init_default_audio_ciph(default_audio_ciph_table)


cdef class HcaDecrypter:
	cdef unsigned char[0x100] _ciph_table

	def __init__(self, unsigned long key1, unsigned long key2):
		cdef unsigned char* _ciph_table
		cdef unsigned long long i
		cdef unsigned long long j
		cdef unsigned char tmp1
		cdef unsigned char v
		cdef unsigned char[7] t1
		cdef unsigned char[16] t2
		cdef unsigned char[0x100] t3
		cdef unsigned char[0x10] t31
		cdef unsigned char[0x10] t32
		cdef unsigned long iTable = 1

		_ciphTable = self._ciph_table
		if key1 == 0:
			key2 -= 1
		key1 -= 1
		for i in range(7):
			t1[i] = key1
			key1 = key1 >> 8 | key2 << 24
			key2 >>= 8

		t2 = [t1[1], t1[1] ^ t1[6], t1[2] ^ t1[3],
			t1[2], t1[2] ^ t1[1], t1[3] ^ t1[4],
			t1[3], t1[3] ^ t1[2], t1[4] ^ t1[5],
			t1[4], t1[4] ^ t1[3], t1[5] ^ t1[6],
			t1[5], t1[5] ^ t1[4], t1[6] ^ t1[1],
			t1[6]]

		init56_create_table(t31, t1[0])
		# Create Table
		for i in range(0x10):
			init56_create_table(t32, t2[i])
			v = t31[i] << 4
			for j in range(sizeof(t32)):
				tmp1 = t32[j]
				t3[i * 0x10 + j] = v | tmp1

		# CIPHテーブル
		for i in range(0x100):
			v = v + 0x11
			tmp1 = t3[v]
			iTable += 1
			if tmp1 != 0 and tmp1 != 0xFF:
				_ciphTable[iTable] = tmp1
		_ciphTable[0] = 0
		_ciphTable[0xFF] = 0xFF

	def decrypt(self, unsigned char* data, unsigned long long size, unsigned int type):
		cdef unsigned char* _ciph_table
		cdef unsigned short sum
		with boundscheck(False):
			if type == 0:
				return
			elif type == 1:
				_ciph_table = default_audio_ciph_table
			elif type == 65:
				_ciph_table = self._ciph_table
			else:
				return -1
			with nogil:
				for i in range(size):
					data[i] = _ciph_table[data[i]]
			sum = self.check_sum(data, size - 2)
			data[size - 1] = sum >> 8
			data[size - 2] = sum & 0xff
		return data[:size]

	cdef unsigned short check_sum(self, unsigned char* data, unsigned long long size):
		cdef unsigned long long i 
		cdef unsigned short sum
		cdef unsigned short[0x100] v = [0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011, 0x8033, 0x0036, 0x003C, 0x8039, 0x0028,
			0x802D, 0x8027, 0x0022,
			0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D, 0x8077, 0x0072, 0x0050, 0x8055, 0x805F, 0x005A, 0x804B,
			0x004E, 0x0044, 0x8041,
			0x80C3, 0x00C6, 0x00CC, 0x80C9, 0x00D8, 0x80DD, 0x80D7, 0x00D2, 0x00F0, 0x80F5, 0x80FF, 0x00FA, 0x80EB,
			0x00EE, 0x00E4, 0x80E1,
			0x00A0, 0x80A5, 0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1, 0x8093, 0x0096, 0x009C, 0x8099, 0x0088,
			0x808D, 0x8087, 0x0082,
			0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197, 0x0192, 0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB,
			0x01AE, 0x01A4, 0x81A1,
			0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB, 0x01FE, 0x01F4, 0x81F1, 0x81D3, 0x01D6, 0x01DC, 0x81D9, 0x01C8,
			0x81CD, 0x81C7, 0x01C2,
			0x0140, 0x8145, 0x814F, 0x014A, 0x815B, 0x015E, 0x0154, 0x8151, 0x8173, 0x0176, 0x017C, 0x8179, 0x0168,
			0x816D, 0x8167, 0x0162,
			0x8123, 0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132, 0x0110, 0x8115, 0x811F, 0x011A, 0x810B,
			0x010E, 0x0104, 0x8101,
			0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D, 0x8317, 0x0312, 0x0330, 0x8335, 0x833F, 0x033A, 0x832B,
			0x032E, 0x0324, 0x8321,
			0x0360, 0x8365, 0x836F, 0x036A, 0x837B, 0x037E, 0x0374, 0x8371, 0x8353, 0x0356, 0x035C, 0x8359, 0x0348,
			0x834D, 0x8347, 0x0342,
			0x03C0, 0x83C5, 0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1, 0x83F3, 0x03F6, 0x03FC, 0x83F9, 0x03E8,
			0x83ED, 0x83E7, 0x03E2,
			0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7, 0x03B2, 0x0390, 0x8395, 0x839F, 0x039A, 0x838B,
			0x038E, 0x0384, 0x8381,
			0x0280, 0x8285, 0x828F, 0x028A, 0x829B, 0x029E, 0x0294, 0x8291, 0x82B3, 0x02B6, 0x02BC, 0x82B9, 0x02A8,
			0x82AD, 0x82A7, 0x02A2,
			0x82E3, 0x02E6, 0x02EC, 0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2, 0x02D0, 0x82D5, 0x82DF, 0x02DA, 0x82CB,
			0x02CE, 0x02C4, 0x82C1,
			0x8243, 0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252, 0x0270, 0x8275, 0x827F, 0x027A, 0x826B,
			0x026E, 0x0264, 0x8261,
			0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E, 0x0234, 0x8231, 0x8213, 0x0216, 0x021C, 0x8219, 0x0208,
			0x820D, 0x8207, 0x0202]
		with nogil:
			with boundscheck(False):
				for i in range(size):
					sum = sum << 8 ^ v[sum >> 8 ^ data[i]]
		return sum


cdef unsigned char* init56_create_table(unsigned char* table, unsigned char key):
	cdef int mul = (key & 1) << 3 | 5
	cdef int add = key & 0xE | 1
	key >>= 4
	for i in range(0x10):
		key = key * mul + add
		table[i] = key
