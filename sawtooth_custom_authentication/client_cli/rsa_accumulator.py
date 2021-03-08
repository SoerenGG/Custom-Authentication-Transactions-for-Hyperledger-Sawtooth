from os import urandom
from math import log2, ceil, floor
from Crypto.Util import number
from hashlib import sha256, shake_256
from typing import Tuple, Union, Iterable
from collections import namedtuple
from dataclasses import dataclass
import operator
import math
import hashlib
from Crypto import Random
import sys



class RSA2048_Accumulator():
    def __init__(self, elements):
        # using script gen_lambda_prime.py to generate rsa numbers

        self.bit_size = 2048
        # 1024 prime p
        self.p = 113670207059472357294514906434140228244224371158243706157752108233778974655713740513597953023188318667552954790790638395628526516329951545235369685235873350786560803494607526623162240272656430745550814082183865195966354201453031082228756766059602964431448110328722449965222902737515202809785178422613978502931
        # 1024 prime p
        self.q = 147265752317501722089328894904235088512725069240326262228659935076191725881274747935516458170799993276674582560393284210244971044740643535655999236410631503013658496964673463033170806886301792420341388695529929848329162517216968731395576588606412638961088195061836057016453714451935432698443875700575056161069
        # 2048 bit N as RSA modulus p*q = N
        self.N = 16739728558699391911822487003799290775719365607538691037232220713757382176565946751059082882141631611098534251238501248016564261277809784947486006859170443128299662238925543090741122401455308789259340742236936696983791412289788877626507217895669058048736288380565441381607358151896005998515472554392145192875871118544996000971245529197829374877403983235150658268815562413283974314887615452315005396127544578045775189061277974328030458361944837246404048304138744948782623840402590497542900521385713890679906547076127719010280655357233572490215883547810102333526480980011508520503945097174448707895057050692392624593239
        # PHI (p-1)(q-1)
        self.phi = 16739728558699391911822487003799290775719365607538691037232220713757382176565946751059082882141631611098534251238501248016564261277809784947486006859170443128299662238925543090741122401455308789259340742236936696983791412289788877626507217895669058048736288380565441381607358151896005998515472554392145192875610182585619026891861685396490999560647033794752088300429150369974003614350626963865890984933556266101547651710094051722156960800874242165512679382492240094982404539943309507886567474226755667514014344298413923965985138638563572676591550193144086730133944674620950013522268479984998072386827996569203589929240
        # g=3 works, look at the script pick_g-2.py
        self.g=3
        # squaring g mod N
        self.g_acc=9
        # generate x elements, hash to primes
        self.tails = elements
        self.modulus = self.N
        if len(elements) > 0:
            self.value = pow(self.g_acc, elements[0], self.modulus)
            for x in elements[1:]:
                self.value = pow(self.value, x, self.modulus)
        else:
            self.value = self.g_acc

    def add(self, x):
        if x not in self.tails:
            old_value = self.value
            self.tails.append(x)

            self.value = pow(old_value, x, self.modulus) 
            return self.value

    def remove(self, x):
        if x in self.tails:
            old_value = self.value
            self.tails.remove(x)

            invers = pow(x, -1, self.phi)
            result = pow(self.value, invers, self.modulus)
            self.value = result
            return result

    def gen_witness(self, x_new):
        wit = self.g_acc
        for x in self.tails:
            if x == x_new:
                continue
            wit = pow(wit, x, self.modulus)
        return wit

    def verify_membership(self, wit_t, x_t):
        if pow(wit_t, x_t, self.modulus) == self.value:
            return True
        else:
            return False

    def get_modulus(self):
        return self.modulus

    def get_acc_value(self):
        return self.value

if __name__ == "__main__":


    # 511 bit p' und q'
    # security parameter
    # security_lambda1024 = 80
    security_lambda2048 = 128
    timer_repetition = 10

    # accumulator evaluation
    acc = RSA2048_Accumulator([])
    # acc = RSA1024_Accumulator([])
    print("acc_t0:", acc.value)

    # generate primes
    x1 = number.getPrime(security_lambda2048, urandom)
    x2 = number.getPrime(security_lambda2048, urandom)
    x3 = number.getPrime(security_lambda2048, urandom)
    x4 = number.getPrime(security_lambda2048, urandom)

    acc.add(x1)
    acc.add(x2)
    acc.add(x3)
    wit1= acc.gen_witness(x1)
    print(acc.verify_membership(wit1, x1))
    '''# adding primes
    acc.add(xi)
    acc_t1 = acc.value
    print("acc_t1:", acc_t1)

    # adding primes
    acc.add(testp)
    acc_t2 = acc.value
    print("acc_t2:", acc_t2)

    # generate witness
    wit = acc.gen_witness(testp)
    wit2 = acc.gen_witness(xi)

    # verify witness
    print(acc.verify_membership(wit, testp)) # True
    print(acc.verify_membership(wit2, xi)) # True
    print(acc.verify_membership(wit, xi)) # False

    # remove element
    acc.remove(testp)
    new_acc_t1 = acc.value
    print("new_acc_t1:", new_acc_t1)
    print("compare acc_t1 with new_acc_t1 (must be equal):", acc_t1==new_acc_t1)

    acc.remove(xi)
    print("acc_t0", acc.value)


    # timing
    start = timer()
    end = timer()
    tt = 1000 * (end - start)
    print("timing example (in ms):", tt)
'''