# PyCriUsm
a python library to decrypt and demux Honkai: Star Rail cutscene video. In theory, it can demux any of the encrypted Usm file. But I only adapted to HSR..

The decryption module was written in cython so that we can achieve a speed 5 to 7 times faster than WannaCRI and nearly as fast as GI-Cutscene.

Refer to [WannaCRI](https://github.com/donmai-me/WannaCRI) and [GI-Cutscene](https://github.com/ToaHartor/GI-cutscenes)

## Build Cython code

Enter the repository and run this command

```python setup.py build_ext --inplace```

## Example

```	
def extract_video(video_path, output_dir, key1, key2):
	a = UsmDemuxer(video_path, key, True)
	video_name, audio_names = a.export(output_dir)
	return video_name, audio_names
```

## Roadmap

- [x] USM decryption support
- [ ] HCA decryption support
- [ ] More flexable and powerful option to control usm chunks

