from slowapi import Limiter
from slowapi.util import get_remote_address

# 初始化 Limiter
# key_func=get_remote_address 根據使用者的 IP 來進行計數
limiter = Limiter(key_func=get_remote_address)