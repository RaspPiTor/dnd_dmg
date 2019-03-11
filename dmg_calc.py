import random
def generate_dmg(dmg_dice, effects):
    rolls = []
    for _ in range(5000):
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
    dmg = []
    hit_die_list = []
    for i in range(2000):
        roll = random.randint(1,21)
        if "halfling" in effects:
            if roll == 1:
                roll = random.randint(1,21)
                if "disadvantage" in effects:
                    roll = min(roll, random.randint(1, 21))
                elif "advantage" in effects:
                    roll = max(roll, random.randint(1, 21))
            else:
                if "disadvantage" in effects:
                    new = random.randint(1, 21)
                    if new == 1:
                        new = random.randint(1, 21)
                    roll = min(roll, new)
                elif "advantage" in effects:
                    new = random.randint(1, 21)
                    if new == 1:
                        new = random.randint(1, 21)
                    roll = max(roll, new)
        else:
            if "disadvantage" in effects:
                roll = min(roll, random.randint(1, 21))
            elif "advantage" in effects:
                roll = max(roll, random.randint(1, 21))
        hit_die_list.append(roll)
    for hit_die in hit_die_list:
        if hit_die + hit_bonus >= ac:
            dmg.extend(on_hit.copy())
        else:
            dmg.extend([0] * len(on_hit))
    dmg.sort()
    mean = sum(dmg)/len(dmg)
    lq = dmg[round(len(dmg)/4)]
    median = dmg[round(len(dmg)/2)]
    uq = dmg[round(len(dmg)*3/4)]
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
