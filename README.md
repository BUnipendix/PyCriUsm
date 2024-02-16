# PyCriUsm
a python library to decrypt and demux HSR cutscene video. In theory, it can demux any of the encrypted Usm file. But I only adapted to HSR..

The decryption module was written in cython so that we can achieve a speed 10x to 13x faster than WannaCRI and 1.4x faster than GI-Cutscene.

Refer to [WannaCRI](https://github.com/donmai-me/WannaCRI) and [GI-Cutscene](https://github.com/ToaHartor/GI-cutscenes)

## Build Cython code

Enter the repository and run this command

```python setup.py build_ext --inplace```

## Example

```	
import asyncio
from pycriusm import extract_usm
videos, audios = asyncio.run(extract_usm(video_path, output_folder, is_async=True))
```

## Roadmap

- [x] USM decryption support
- [ ] HCA decryption support(Used by GI)
- [ ] More flexable and powerful option to control usm chunks

