import logging


logger = logging.getLogger('CriUsmDemuxer')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)-4s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)