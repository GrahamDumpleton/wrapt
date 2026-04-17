"""
Type-check coverage for container-protocol usage of ObjectProxy:
len(), indexing, containment, iteration, reversal.
"""

import wrapt

list_proxy: wrapt.ObjectProxy[list[int]] = wrapt.ObjectProxy([1, 2, 3])

# Sized.
size: int = len(list_proxy)

# Container.
present: bool = 1 in list_proxy

# Iterable (via ObjectProxy.__iter__).
for _item in list_proxy:
    pass

# Reversible.
reversed_items = list(reversed(list_proxy))

# Indexing.
item = list_proxy[0]
list_proxy[0] = 99
del list_proxy[0]
