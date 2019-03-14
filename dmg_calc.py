import itertools
import functools
import time
import math

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


@functools.lru_cache(maxsize=32)
def generate_rolls(die, number):
    if number == 1:
        return (1, tuple([1]*die))
    tables = []
    while number > 0:
        now = int(math.log(number, 2))
        number -= 2**now
        if now == 0:
            tables.append((1, tuple([1]*die)))
        else:
            current = generate_rolls(die, 2**(now-1))
            tables.append(combine_tables(current, current))
    while len(tables) > 1:
        new = []
        for i in range(0, len(tables), 2):
            if len(tables[i:i+2]) == 2:
                new.append(combine_tables(tables[i], tables[i+1]))
            else:
                new.append(tables[i])
        tables = new
    return tables[0]
    

@functools.lru_cache(maxsize=32)
def generate_dmg(dmg_bonus, dmg_dice, effects, outcomes):
    if len(dmg_dice) == 0:
        return (0, ())
    tables = []
    for die in set(dmg_dice):
        minn, content = generate_rolls(die, dmg_dice.count(die))
        tables.append((minn + dmg_bonus, content))
    table = tables[0]
    for t in tables[1:]:
        table = combine_tables(table, t)
    return table

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
        
@functools.lru_cache(maxsize=32)
def dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, effects, outcomes):
    minn, on_hit = generate_dmg(dmg_bonus, dmg_dice, effects, outcomes)
    hits, misses = generate_hits(hit_bonus, ac, effects)
    on_hit = list(on_hit)
    old_sum = sum(on_hit)
    for i in range(len(on_hit)):
        on_hit[i] *= hits
    if minn > 0:
        on_hit[:0] = [0] * minn
    on_hit[0] = misses*old_sum
    return clean((0, on_hit))

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


def attack_calc(ac, *attacks, outcomes=100000, n=10, timeslice=0.1):
    if not attacks:
        return iter(())
    start = time.time()
    if n > outcomes:
        return ValueError
    tables = []
    total_work = len(attacks) * 2
    for i, (hit_bonus, dmg_dice, dmg_bonus, effects) in enumerate(attacks):
        tables.append(dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, effects,
                            outcomes))
        if time.time() - start > timeslice:
            yield False, i*outcomes/len(attacks), total_work, None
            start = time.time()
    
    table = tables[0]
    for i, t in enumerate(tables[1:]):
        table = combine_tables(table, t)
        if time.time() - start > timeslice:
            yield False, i + len(attacks), total_work, None
            start = time.time()
    yield True, total_work, total_work, gen_stats(table, n)
