import logging

ss_logger = logging.getLogger('sentient-sims')

ss_logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('sentient-sims.log')
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

ss_logger.addHandler(file_handler)
ss_logger.addHandler(console_handler)
