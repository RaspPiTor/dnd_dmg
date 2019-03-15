import itertools
import functools
import time
import math

@functools.lru_cache(maxsize=32)
def clean(table):
    minn, content = table
    content = list(content)
    while content[0] == 0:
        del content[0]
        minn += 1
    while content[-1] == 0:
        del content[-1]
    found = True
    while found:
        found = False
        try:
            smallest = min(x for x in content if x not in (0,1))
            for i in range(2, int(math.sqrt(smallest))):
                if all(x % i == 0 for x in content):
                    found = True
                    for z in range(len(content)):
                        content[z] //= i
                    break
            if not found:
                 if all(x % smallest == 0 for x in content):
                    found = True
                    for z in range(len(content)):
                        content[z] //= smallest
        except ValueError:
            break
    return minn, tuple(content)
    

@functools.lru_cache(maxsize=32)
def combine_tables(table1, table2):
    minn = table1[0] + table2[0]
    result = [0]*((len(table1[1]) + len(table2[1])) - 1)
    
    for i1, x1 in enumerate(table1[1]):
        for i2, x2 in enumerate(table2[1]):
            result[i1+i2] += x1 * x2
    return (minn, tuple(result))

def generate_rolls(die, number):
    base = (1, tuple([1]*die))
    tables = [base] * number
    while len(tables) > 1:
        new = []
        for i in range(0, len(tables), 2):
            if len(tables[i:i+2]) == 2:
                new.append(combine_tables(tables[i], tables[i+1]))
                if tables[i] != tables[i+1]:
                    yield False, ()
            else:
                new.append(tables[i])
        tables = new
        yield False, ()
    yield True, tables[0]
    

def generate_dmg(dmg_bonus, dmg_dice, effects):
    if len(dmg_dice) == 0:
        return (0, ())
    tables = []
    for die in set(dmg_dice):
        for done, result in generate_rolls(die, dmg_dice.count(die)):
            if done:
                minn, content = result
                tables.append((minn + dmg_bonus, content))
                print('Added')
            yield False, ()
    if len(tables) == 0:
        print(dmg_bonus, dmg_dice, effects, set(dmg_dice))
    table = tables[0]
    for t in tables[1:]:
        table = combine_tables(table, t)
        yield False, ()
    yield True, table

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
    for done, result in dmg_iter:
        if done:
            minn, on_hit = result
        yield False, ()
    hits, misses = generate_hits(hit_bonus, ac, effects)
    yield False, ()
    on_hit = list(on_hit)
    old_sum = sum(on_hit)
    for i in range(len(on_hit)):
        on_hit[i] *= hits
    if minn > 0:
        on_hit[:0] = [0] * minn
    on_hit[0] = misses*old_sum
    yield False, ()
    yield True, clean((0, tuple(on_hit)))

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


def attack_calc(ac, *attacks, n=10, timeslice=0.05):
    if not attacks:
        return iter(())
    start = time.time()
    tables = []
    total_work = len(set(attacks)) + len(attacks)
    amount_done = 0
    for i, (hit_bonus, dmg_dice, dmg_bonus, effects) in enumerate(attacks):
        dmg_iter = dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, effects)
        for done, result in dmg_iter:
            if done:
                if result not in tables:
                    amount_done += 1
                tables.append(result)
            if time.time() - start > timeslice:
                yield False, amount_done, total_work, None
                start = time.time()
    yield False, len(attacks), total_work, None
    while len(tables) > 1:
        new = []
        for i in range(0, len(tables), 2):
            if len(tables[i:i+2]) == 2:
                new.append(combine_tables(tables[i], tables[i+1]))
                amount_done += 1
                if time.time() - start > timeslice:
                    yield False, amount_done, total_work, None
                    start = time.time()
            else:
                new.append(tables[i])
        tables = new
    yield True, total_work, total_work, gen_stats(tables[0], n)
