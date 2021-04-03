save_after_return = False
progressive_response = False
use_timeouts = True
inf_timeout = 10**6  # this might be interpreted as 1 million seconds or 1 million milliseconds (1000 seconds) depending on the context; we make it large enough that it doesn't matter either way
USE_ASR_ROBUSTNESS_OVERALL_FLAG = True  # enable ASR robustness in the entity linker

# This is the max size the entire item that we write to dynamodb
SIZE_THRESHOLD = 400*1024 - 100 # 400 kb - 100 bytes for
