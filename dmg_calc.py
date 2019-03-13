import random
def generate_dmg(dmg_dice, effects):
    rolls = []
    if "great-weapon-fighting" in effects:
        for _ in range(100000):
            roll = []
            for die in dmg_dice:
                n = random.randint(1,die)
                if n in [1,2]:
                    n = random.randint(1,die)
                roll.append(n)
            rolls.append(roll)
    else:
        for _ in range(100000):
            rolls.append([random.randint(1, die) for die in dmg_dice])
    return rolls
        

def dmg_calc(hit_bonus, dmg_dice, dmg_bonus, ac, *effects):
    rolls = generate_dmg(dmg_dice, effects)
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

print('fireball', dmg_calc(4, [8]*8, 0, 16))
print('Meteor Swarm', dmg_calc(5, [6]*40, 0, 16))
print('Undead Swarm', dmg_calc(5, [6]*116, 232, 16))
