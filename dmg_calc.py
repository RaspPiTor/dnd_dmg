import itertools
import functools
import time
import math

def combine_tables(table1, table2, cache={}):
    if (table1, table2) in cache:
        yield True, cache[(table1, table2)], 1, 1
        return
    minn = table1[0] + table2[0]
    result = [0]*((len(table1[1]) + len(table2[1])) - 1)
    if table1 == table2:
        table = table1
        for i1, x1 in enumerate(table[1]):
            for i2, x2 in zip(range(i1, len(table[1])), table[1][i1:]):
                if i1 == i2:
                    result[i1+i2] += x1 * x2
                else:
                    result[i1+i2] += x1 * x2 * 2
            if len(table[1]) > 500:
                yield False, (), i1, len(table1[1])
    else:
        for i1, x1 in enumerate(table1[1]):
            for i2, x2 in enumerate(table2[1]):
                result[i1+i2] += x1 * x2
            if len(table2[1]) > 100:
                yield False, (), i1, len(table1[1])
    if len(cache) > 128:
        cache.clear()
    cache[(table1, table2)] = (minn, tuple(result))
    yield True, (minn, tuple(result)), 1, 1

def combine_iter(tables):
    total_work = len(tables)
    while len(tables) > 1:
        new = []
        singles = []
        duplicates = []
        for table in set(tables):
            count = tables.count(table)
            if count > 1:
                duplicates.append((table, count//2))
            if count % 2 == 1:
                singles.append(table)
        next_length = (len(tables) - len(singles))//2 + min(len(singles), 1)
        amount_of_work = len(tables) - next_length
        already_done = total_work - len(tables)
        progress = 0
        for table, count in duplicates:
            progress += count
            now = already_done + progress/amount_of_work
            for done, result, value, maximum in combine_tables(table, table):
                if done:
                    new.extend([result] * count)
                yield False, (), now + value/maximum, total_work
        if singles:
            for i in range(len(singles) - 1):
                progress += 1
                now = already_done + progress/amount_of_work
                combine_singles_iter = combine_tables(singles[-1], singles[-2])
                for done, result, value, maximum in combine_singles_iter:
                    if done:
                        del singles[-1]
                        singles[-1] = result
                    yield False, (), now + value/maximum, total_work
            if singles:
                new.append(singles[0])
        tables = new
        if len(tables) != next_length:
            print(len(tables), next_length)
    yield True, tables[0], 1, 1

def generate_rolls(die, number, cache={}):
    if (die, number) in cache:
        yield True, cache[(die, number)], 1, 1
        return
    base = (1, tuple([1]*die))
    tables = [base] * number
    for done, result, value, maximum in combine_iter(tables):
        if done:
            if len(cache) > 128:
                cache.clear()
            cache[(die, number)] = result
        yield done, result, value, maximum


def generate_dmg(dmg_bonus, dmg_dice, effects, cache={}):
    if (dmg_bonus, dmg_dice, effects) in cache:
        yield True, cache[(dmg_bonus, dmg_dice, effects)], 1, 1
        return
    if len(dmg_dice) == 0:
        yield True, (0, ()), 1, 1
        return
    tables = []
    total_work = len(set(dmg_dice)) * 2
    for i, die in enumerate(set(dmg_dice)):
        count = dmg_dice.count(die)
        for done, result, value, maximum in generate_rolls(die, count):
            if done:
                minn, content = result
                tables.append((minn + dmg_bonus, content))
            yield False, (), i + value/maximum, total_work
    progress = len(set(dmg_dice))
    for done, result, value, maximum in combine_iter(tables):
        if done:
            if len(cache) > 128:
                cache.clear()
            cache[(dmg_bonus, dmg_dice, effects)] = result
        yield done, result, progress + value/maximum * progress, total_work

@functools.lru_cache(maxsize=32)
def generate_hits(hit_bonus, ac, effects):
    hits = 0
    total = 0
    for roll, second, third in itertools.product(range(1, 21), range(1, 21),
                                                 range(1, 21)):
        if "halfling" in effects:
            if roll == 1:
                roll = second
                if "disadvantage" in effects:
                    roll = min(roll, third)
                elif "advantage" in effects:
                    roll = max(roll, third)
            else:
                if "disadvantage" in effects:
                    new = second
                    if new == 1:
                        new = third
                    roll = min(roll, new)
                elif "advantage" in effects:
                    new = second
                    if new == 1:
                        new = third
                    roll = max(roll, new)
        else:
            if "disadvantage" in effects:
                roll = min(roll, second)
            elif "advantage" in effects:
                roll = max(roll, third)
        if roll + hit_bonus >= ac:
            hits += 1
        total += 1
    misses = total - hits
    found = True
    while found:
        found = False
        for i in range(2, max(hits, misses)):
            if hits % i == 0 and misses % i == 0:
                hits //= i
                misses //= i
                found = True
                break
    return hits, misses


def dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, effects):
    dmg_iter = generate_dmg(dmg_bonus, dmg_dice, effects)
    for done, result, value, maximum in dmg_iter:
        if done:
            minn, on_hit = result
        yield False, (), value, maximum
    hits, misses = generate_hits(hit_bonus, ac, effects)
    on_hit = list(on_hit)
    old_sum = sum(on_hit)
    for i in range(len(on_hit)):
        on_hit[i] *= hits
    if minn > 0:
        on_hit[:0] = [0] * minn
    on_hit[0] = misses*old_sum
    yield True, (0, tuple(on_hit)), 1, 1

def gen_stats(table, n=10):
    minn, contents = table
    total = sum(contents)
    mean = sum((i + minn) * x for i, x in enumerate(contents))/total
    chunks = []
    for i in range(1, n+1):
        pos = contents[0]
        x = 0
        while pos < total//n * i:
            x += 1
            pos += contents[x]
        chunks.append(x + minn)
    return mean, chunks


def attack_calc(ac, *attacks, n=10, timeslice=0.1):
    if not attacks:
        return iter(())
    start = time.time()
    tables = []
    unique = set(attacks)
    total_work = len(unique) + len(attacks)
    
    for i, (hit_bonus, dmg_dice, dmg_bonus, effects) in enumerate(unique):
        dmg_iter = dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, effects)
        for done, result, value, maximum in dmg_iter:
            if time.time() - start > timeslice:
                yield False, i + value/maximum, total_work, None
                start = time.time()
            if done:
                tables.extend([result] * attacks.count(
                    (hit_bonus, dmg_dice, dmg_bonus, effects)))
    progress = len(unique)
    yield False, progress, total_work, None
    for done, result, value, maximum, in combine_iter(tables):
        if done:
            yield True, total_work, total_work, gen_stats(result, n)
        else:
            if time.time() - start > timeslice:
                yield False, progress + value/maximum * progress, total_work, None
                start = time.time()
