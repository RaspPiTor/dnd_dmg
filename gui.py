import tkinter.ttk as ttk
import tkinter as tk
import re

import dmg_calc

class GUIAttack():
    def __init__(self, master, n, row=0):
        self.hit_bonus = ttk.Entry(master)
        self.dmg_dice = ttk.Entry(master)
        self.dmg_bonus = ttk.Entry(master)
        self.attack_count = ttk.Entry(master)
        self.effects = ttk.Entry(master)
        self.button = ttk.Button(master, text='X', command=self.destroy_button)
        self.n = n
        self.master = master
        self.move(row)
    def destroy_button(self):
        self.hit_bonus.destroy()
        self.dmg_dice.destroy()
        self.dmg_bonus.destroy()
        self.effects.destroy()
        self.attack_count.destroy()
        self.button.destroy()
        self.master.handle_remove_of_attack(self.n)
    def move(self, row):
        self.hit_bonus.grid(row=row, column=0, sticky='nesw')
        self.dmg_dice.grid(row=row, column=1, sticky='nesw')
        self.dmg_bonus.grid(row=row, column=2, sticky='nesw')
        self.attack_count.grid(row=row, column=3, sticky='nesw')
        self.effects.grid(row=row, column=4, sticky='nesw')
        self.button.grid(row=row, column=5, sticky='nesw')
    def get_attack(self):
        try:
            hit_bonus = int(self.hit_bonus.get())
        except ValueError:
            self.hit_bonus.delete(0, 'end')
            self.hit_bonus.insert(0, '0')
            hit_bonus = 0
        dice = re.findall('(?:([0-9]+)d)?([0-9]+)', self.dmg_dice.get())
        dmg_dice = []
        for n, die in dice:
            if n:
                dmg_dice.extend([int(die)] * int(n))
            else:
                dmg_dice.append(int(die))
        dmg_dice.sort()
        dmg_dice = tuple(dmg_dice)
        new = ' '.join('%sd%s' % (dmg_dice.count(i), i)
                       for i in sorted(set(dmg_dice)))
        if self.dmg_dice.get() != new:
            self.dmg_dice.delete(0, 'end')
            self.dmg_dice.insert(0,
                                 ' '.join('%sd%s'
                                          % (dmg_dice.count(i), i)
                                          for i in sorted(set(dmg_dice))))
        try:
            dmg_bonus = int(self.dmg_bonus.get())
        except ValueError:
            self.dmg_bonus.delete(0, 'end')
            self.dmg_bonus.insert(0, '0')
            dmg_bonus = 0
        try:
            attack_count = int(self.attack_count.get())
        except ValueError:
            self.attack_count.delete(0, 'end')
            self.attack_count.insert(0, '1')
            attack_count = 1
        effects = self.effects.get()
        return hit_bonus, dmg_dice, dmg_bonus, attack_count, effects
        

class GUIAttacks(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        ttk.Label(self, text='Hit Bonus:').grid(row=0, column=0, sticky='w')
        ttk.Label(self, text='Damage Dice:').grid(row=0, column=1, sticky='w')
        ttk.Label(self, text='Damage Bonus:').grid(row=0, column=2, sticky='w')
        ttk.Label(self, text='Attack Count:').grid(row=0, column=3, sticky='w')
        ttk.Label(self, text='Effects:').grid(row=0, column=4, sticky='w')
        self.attacks = []
        self.add_button = ttk.Button(self, text='Add Attack', command=self.add_attack)
        self.add_button.columnconfigure(0, weight=1)
        self.add_button.grid(row=2, columnspan=4, sticky='n')
        self.add_attack()
    def handle_attacks(self):
        for i, attack in enumerate(self.attacks):
            attack.move(row=i+1)
            attack.n = i
        self.add_button.grid(row=i+2)
    def handle_remove_of_attack(self, n):
        del self.attacks[n]
        if len(self.attacks) == 0:
            self.add_attack()
        self.handle_attacks()
    def add_attack(self):
        attack = GUIAttack(self, 0)
        self.attacks.append(attack)
        self.handle_attacks()
    def get_attacks(self):
        attacks = []
        for i in self.attacks:
            hit_bonus, dmg_dice, dmg_bonus, attack_count, effects = i.get_attack()
            for _ in range(attack_count):
                if dmg_dice:
                    attacks.append((hit_bonus, dmg_dice, dmg_bonus, effects))
        return attacks
    

class GUI(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        ttk.Label(self, text='Enemy AC:').grid(row=0, column=0, sticky='w')
        self.ac = ttk.Entry(self)
        self.ac.grid(row=0, column=1, sticky='new')
        self.attacks = GUIAttacks(self)
        self.attacks.columnconfigure(1, weight=1)
        self.attacks.grid(row=1, column=0, columnspan=5)
        self.button = ttk.Button(self, text='Calculate', command=self.calculate)
        self.button.grid(row=2, columnspan=4)
        self.progress = ttk.Progressbar(self)
        self.progress.grid(row=0, column=6, sticky='nesw')
        self.dmg_calc = iter(())
        self.background = False
        self.running_calc = False
        self.current_hash = 0
        self.refresh()
    def calculate(self, background=False):
        try:
            ac = int(self.ac.get())
        except ValueError:
            if not background:
                self.ac.delete(0, 'end')
                self.ac.insert(0, '10')
            ac = 10
        attacks = self.attacks.get_attacks()
        if background:
            if hash((ac, tuple(attacks))) == self.current_hash:
                return
        if self.running_calc == False or self.background:
            self.current_hash = hash((ac, tuple(attacks)))
            self.background = background
            if not background:
                self.progress['value'] = 0
                self.progress['maximum'] = 1
            self.running_calc = True
            self.dmg_calc = dmg_calc.attack_calc(ac, *attacks)
            if not background:
                self.button['state'] = 'disabled'
            
    def refresh(self):
        if self.running_calc:
            try:
                done, value, maximum, result = next(self.dmg_calc)
                if not self.background:
                    self.progress['value'] = value
                    self.progress['maximum'] = maximum
                    if value > maximum:
                        print('Too high value: %s %s' % (value, maximum))
                    if done:
                        print(result)
            except StopIteration:
                del self.dmg_calc
                self.running_calc = False
                self.button['state'] = 'normal'
        else:
            self.calculate(True)
        self.after(10, self.refresh)
gui = GUI()
gui.grid()
gui.mainloop()
