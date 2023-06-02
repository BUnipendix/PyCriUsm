from threading import Thread


def make_thread(func, *args, is_daemon=False, **kwargs):
	thread = Thread(target=func, args=args, kwargs=kwargs, daemon=is_daemon)
	thread.start()
	return thread