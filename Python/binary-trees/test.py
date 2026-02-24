from math import log2
from multiprocessing import cpu_count
from itertools import chain

# Import all needed functions from the original benchmark
from types import GeneratorType

from binarytrees import make_tree, check_tree, make_check, get_argchunks


# Now the test cases

# Test 1: make_tree at depth 0
tree0 = make_tree(0)
assert tree0 == (None, None), "Depth 0 should produce leaf node (None, None)"

# Test 2: make_tree at depth 1
tree1 = make_tree(1)
assert tree1 == ((None, None), (None, None)), "Depth 1 should produce two leaves"

# Test 3: check_tree on depth 0
assert check_tree(tree0) == 1, "check_tree should return 1 for a single leaf"

# Test 4: check_tree on depth 1
assert check_tree(tree1) == 3, "check_tree on depth 1 should return 3 (1 + 1 + 1)"

# Test 5: make_check on depth 2
assert make_check((0, 2)) == 7, "Depth 2 tree has 7 nodes"

# Test 6: make_check returns same result for any i
assert make_check((5, 2)) == make_check((999, 2)), "make_check ignores 'i' value"

# Test 7: get_argchunks yields correct number of chunks and content
chunks = list(get_argchunks(4, 3, chunksize=2))
assert isinstance(chunks, list), "get_argchunks should return a generator/list"
assert len(chunks) == 2, "4 elements with chunksize 2 should yield 2 chunks"
assert all(isinstance(chunk, list) for chunk in chunks), "Each chunk should be a list"
assert all(len(chunk) == 2 for chunk in chunks), "Each chunk should have 2 items"

# Test 8: get_argchunks with no elements
empty_chunks = list(get_argchunks(0, 3, chunksize=2))
assert empty_chunks == [], "No iterations should yield no chunks"

# Test 9: Large depth tree check is consistent
depth = 5
tree = make_tree(depth)
expected_nodes = 2 ** (depth + 1) - 1
assert check_tree(tree) == expected_nodes, f"Depth {depth} should have {expected_nodes} nodes"

# Test 10: get_argchunks chunks add up to total
N = 10
all_chunks = list(get_argchunks(N, 3, chunksize=4))
total_pairs = sum(len(chunk) for chunk in all_chunks)
assert total_pairs == N, f"Expected {N} pairs, got {total_pairs}"

# Test 11: check_tree handles deeply nested trees
deep_tree = make_tree(10)
assert check_tree(deep_tree) == 2047, "Depth 10 tree should have 2047 nodes"

# Print if all tests pass
print("All tests passed.")
