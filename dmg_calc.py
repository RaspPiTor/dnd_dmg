import random
def generate_dmg(dmg_dice, effects):
    rolls = []
    for _ in range(100000):
        roll = []
        for die in dmg_dice:
            n = random.randint(1,die)
            if "great-weapon-fighting" in effects and n in [1,2]:
                n = random.randint(1,die)
            roll.append(n)
        rolls.append(roll)
    return rolls
        

def dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, *effects):
    rolls = generate_dmg(dmg_dice, effects)
    on_hit = []
    for roll in rolls:
        on_hit.append(sum(roll) + dmg_bonus)
    on_hit.sort()
    on_hit.reverse()
    dmg = []
    hit_die_list = []
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
        hit_die_list.append(roll)
    hit_die_chances = {}
    for i in range(1, 21):
        hit_die_chances[i] = hit_die_list.count(i)
    hits = 0
    total = 0
    for hit_die in range(1, 21):
        if hit_die + hit_bonus >= ac:
            hits += hit_die_chances[hit_die]
        total += hit_die_chances[hit_die]
    mean = sum(on_hit)/len(on_hit)*hits/total
    try:
        lq = on_hit[round(3/4*len(on_hit)*total/hits)]
    except IndexError:
        lq = 0
    try:
        median = on_hit[round(1/2*len(on_hit)*total/hits)]
    except IndexError:
        median = 0
    try:
        uq = on_hit[round(1/4*len(on_hit)*total/hits)]
    except IndexError:
        uq = 0
    return mean, (lq, median, uq)

import itertools
base = 4, [6, 6], 4, 16
gwfighter = -1, [6,6], 14, 16
for name, modifier in zip(['plain', 'great-weapon-fighter'], [base, gwfighter]):
    for x in range(4):
        for effects in itertools.combinations(['halfling',
                                               'great-weapon-fighting',
                                               'advantage'], x):
            print(name, effects, dmg_calc(*modifier, *effects))

print('fireball', dmg_calc(5, [8]*8, 0, 16))
