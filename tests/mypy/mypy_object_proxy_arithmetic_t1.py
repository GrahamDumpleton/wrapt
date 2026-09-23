"""
Type-check coverage for arithmetic and numeric-conversion usage of
BaseObjectProxy.
"""

import wrapt

n_proxy: wrapt.BaseObjectProxy[int] = wrapt.BaseObjectProxy(42)

# Binary arithmetic.
_ = n_proxy + 1
_ = n_proxy - 1
_ = n_proxy * 2
_ = n_proxy / 2
_ = n_proxy // 2
_ = n_proxy % 2
_ = divmod(n_proxy, 2)
_ = n_proxy**2
_ = n_proxy << 1
_ = n_proxy >> 1
_ = n_proxy & 1
_ = n_proxy | 1
_ = n_proxy ^ 1

# Reflected arithmetic.
_ = 1 + n_proxy
_ = 1 - n_proxy

# In-place arithmetic.
n_proxy += 1
n_proxy -= 1

# Unary arithmetic.
_ = -n_proxy
_ = +n_proxy
_ = abs(n_proxy)
_ = ~n_proxy

# Numeric conversions.
_ = int(n_proxy)
_ = float(n_proxy)
_ = complex(n_proxy)
_ = bool(n_proxy)
_ = round(n_proxy)

# Bytes / index.
b_proxy: wrapt.BaseObjectProxy[bytes] = wrapt.BaseObjectProxy(b"x")
_ = bytes(b_proxy)

idx_proxy: wrapt.BaseObjectProxy[int] = wrapt.BaseObjectProxy(3)
_ = [1, 2, 3][idx_proxy]
