from sys import argv
from math import factorial
from multiprocessing import cpu_count, Pool
from itertools import islice, starmap

def permutations(n, start, size):
    p = bytearray(range(n))
    count = bytearray(n)

    # precompute factorial values to avoid repeated calls inside the loop
    fact = [1] * n
    f = 1
    for v in range(1, n):
        f *= v
        fact[v] = f

    remainder = start
    v = n - 1
    while v > 0:
        q, remainder = divmod(remainder, fact[v])
        count[v] = q
        for _ in range(q):
            tmp = p[0]
            # rotate left the segment p[0..v] by 1 using slice to reduce Python overhead
            p[:v] = p[1:v+1]
            p[v] = tmp
        v -= 1

    assert(count[1] == 0)
    assert(size < 2 or (size % 2 == 0))

    if size < 2:
        yield p[:]
        return
    else:
        rotation_swaps = [None] * n
        for i in range(1, n):
            r = list(range(n))
            u = 1
            while u <= i:
                tmp = r[0]
                # rotate left the first u elements
                r[:u] = r[1:u+1]
                r[u] = tmp
                u += 1
            swaps = []
            dst = 0
            for src in r:
                if dst != src:
                    swaps.append((dst, src))
                dst += 1
            rotation_swaps[i] = tuple(swaps)

        local_p = p
        local_count = count
        local_rot = rotation_swaps
        while True:
            yield local_p[:]
            local_p[0], local_p[1] = local_p[1], local_p[0]
            yield local_p[:]
            i = 2
            while local_count[i] >= i:
                local_count[i] = 0
                i += 1
            else:
                local_count[i] += 1
                t = local_p[:]
                for dst, src in local_rot[i]:
                    local_p[dst] = t[src]

def alternating_flips_generator(n, start, size):
    maximum_flips = 0
    alternating_factor = 1
    for permutation in islice(permutations(n, start, size), size):
        first = permutation[0]
        if first:
            flips_count = 1
            while True:
                # reverse prefix [0..first] in place to avoid allocations
                i = 0
                j = first
                while i < j:
                    permutation[i], permutation[j] = permutation[j], permutation[i]
                    i += 1
                    j -= 1
                first = permutation[0]
                if not first:
                    break
                flips_count += 1
            if maximum_flips < flips_count:
                maximum_flips = flips_count
            yield flips_count * alternating_factor
        else:
            yield 0
        alternating_factor = -alternating_factor
    yield maximum_flips

def task(n, start, size):
    alternating_flips = alternating_flips_generator(n, start, size)
    return sum(islice(alternating_flips, size)), next(alternating_flips)

def fannkuch(n):
    if n < 0:
        for data in islice(permutations(-n, 0, factorial(-n)), factorial(-n)):
            print(''.join(str(x + 1) for x in data))
    else:
        assert(n > 0)

        task_count = cpu_count()
        total = factorial(n)
        task_size = (total + task_count - 1) // task_count

        if task_size < 20000:
            task_size = total
            task_count = 1

        assert(task_size % 2 == 0)

        task_args = [(n, i * task_size, task_size) for i in range(task_count)]

        if task_count > 1:
            with Pool() as pool:
                checksums, maximums = zip(*pool.starmap(task, task_args))
        else:
            checksums, maximums = zip(*starmap(task, task_args))

        checksum, maximum = sum(checksums), max(maximums)
        print(f"{checksum}\nPfannkuchen({n}) = {maximum}")

if __name__ == "__main__":
    fannkuch(int(argv[1]))