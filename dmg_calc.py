import itertools
import functools
import random
import time

def combine(*dmg, outcomes):
    if len(dmg) == 0:
        return [0] * outcomes
    total = len(dmg[0])
    for i in dmg[1:]:
        total *= len(i)
    if total < outcomes:
        return map(sum, itertools.product(*dmg))
    else:
        for _ in range(outcomes):
            yield sum(random.choice(i) for i in dmg)

@functools.lru_cache(maxsize=32)
def generate_dmg(dmg_dice, effects, outcomes):
    if len(dmg_dice) == 0:
        return [[0]]
    rolls = []
    if "great-weapon-fighting" in effects:
        for _ in range(outcomes):
            roll = []
            for die in dmg_dice:
                n = random.randint(1,die)
                if n in [1,2]:
                    n = random.randint(1,die)
                roll.append(n)
            rolls.append(roll)
    else:
        total = dmg_dice[0]
        for i in dmg_dice[1:]:
            total *= i
        if total < outcomes:
            rolls = list(itertools.product(*[range(1, i+1) for i in dmg_dice]))
        else:
            for _ in range(outcomes):
                rolls.append([random.randint(1, die) for die in dmg_dice])
    return rolls
        
@functools.lru_cache(maxsize=32)
def dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, effects, outcomes):
    rolls = generate_dmg(dmg_dice, effects, outcomes)
    on_hit = []
    for roll in rolls:
        on_hit.append(sum(roll) + dmg_bonus)
    on_hit.sort()
    on_hit.reverse()
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
    hits_to_add = round(outcomes/total*hits)
    reformed_losses = outcomes - hits_to_add
    output = []
    while hits_to_add > len(on_hit):
        output.extend(on_hit)
        hits_to_add -= len(on_hit)
    for _ in range(hits_to_add):
        output.append(random.choice(on_hit))
    output.extend([0] * reformed_losses)
    return output

def clean(output, outcomes, n=10):
    output.sort()
    means = []
    for i in range(n):
        start, end = round(i/n*outcomes), round((i+1)/n*outcomes)
        means.append(round(sum(output[start:end])/(end-start), 2))
    return round(sum(means)/n, 2), means


def attack_calc(ac, *attacks, outcomes=100000, n=10, timeslice=0.1):
    if n > outcomes:
        return ValueError
    dmg = []
    total_work = outcomes * 2
    for i, (hit_bonus, dmg_dice, dmg_bonus, effects) in enumerate(attacks):
        dmg.append(dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, effects,
                            outcomes))
        yield False, i*outcomes/len(attacks), total_work, None
    start = time.time()
    combined = []
    for i, new in enumerate(combine(*dmg, outcomes=outcomes)):
        combined.append(new)
        if time.time() - start > timeslice:
            yield False, i + outcomes, total_work, None
            start = time.time()
        
    yield True, total_work, total_work, clean(combined, outcomes, n)
            


if __name__ == '__main__':
    print('Polearm + great_weapon_fighter', attack_calc(16,[4, [8], 4],
                                                        [-1, [4], 14], outcomes=100))
                                                             
    print('1d4 x 1d4', attack_calc(0,[0, [4], 0],[0, [4], 0], outcomes=1, n=10))
