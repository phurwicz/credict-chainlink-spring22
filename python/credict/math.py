"""
Mathematical support for basic cryptography.
"""

from tqdm import tqdm
from math import sqrt, ceil
from collections import defaultdict


class Factorizer:  # pylint: disable=too-few-public-methods
    """
    A factorizer that makes use of multiple data structures.
    This is intended to be efficient for repeated factorizations.
    """

    def __init__(self, bound=10 ** 12):
        """
        Initialize a cache of factorizations and precompute primes.
        bound -- the bound of numbers that the factorizer is expected to deal with.
        """
        self._tentative_bound = bound
        self._cache = {}
        self._init_primes()

    def _check_bound(self, num):
        if num > self._bound:
            # multiply by 10 to ensure at most log(real_bound) updates
            self._tentative_bound = num * 10
            self._update_primes()

    def _init_primes(self):
        self.list_primes = [2, 3, 5, 7]
        self.set_primes = set(self.list_primes)
        self._update_primes(low=2)
        
    def load_primes(self, path):
        with open(path, "rb") as f:
            self.list_primes = sorted(pickle.load(f))
            self.set_primes = set(self.list_primes)
            self._tentative_bound = self.list_primes[-1] ** 2
            self._update_primes(low=2)
            
    def save_primes(self, path):
        with open(path, "wb") as f:
            pickle.dump(self.list_primes, f)
            
    def _update_primes(self, low=None, high=None):
        """
        Update the list and set of primes, up to some bound.
        Because the primes are calculated all over again, ideally you want to set a reasonable bound at start.
        """
        # we only need primes up to sqrt(bound)
        # if none of those divide a number < bound, that number must be prime
        low = low or self.list_primes[-1]
        high = (high or ceil(sqrt(self._tentative_bound))) + 1
        for _num in tqdm(range(low, high), desc=f"Primes up to {high}"):
            if _num in self.set_primes: continue
            _max_p_for_num = ceil(sqrt(_num))
            for _p in self.list_primes:
                # all possible factors denied -> found a prime
                if _p > _max_p_for_num:
                    self.list_primes.append(_num)
                    self.set_primes.add(_num)
                    break
                # found a factor -> non-prime
                if _num % _p == 0:
                    break
        self._bound = self._tentative_bound

    def _least_divisor(self, num):
        """
        Find the least divisor of a number.
        """
        self._check_bound(num)
        max_p_for_num = ceil(sqrt(num))
        for _p in self.list_primes:
            if num % _p == 0:
                return _p
            # early stopping
            if _p > max_p_for_num:
                return num
        # with check_bound call, num can never be out of range
        return num

    def factorize(self, num):
        """
        Factorize a number.
        """

        self._check_bound(num)
        # case 0: num is too small
        if num < 2:
            return {}
        
        # case 1: num is already factorized
        if num in self._cache.keys():
            return self._cache[num]
        
        # case 2: num is a prime
        if num in self.set_primes:
            factorization = {num: 1}
            self._cache[num] = factorization
            return factorization
        
        # common case: num is a composite number
        divisor = self._least_divisor(num)
        factor = int(num / divisor)
        factorization = defaultdict(int)
        factorization.update(self.factorize(factor))
        factorization[divisor] += 1
        self._cache[num] = factorization
        return factorization


def power_mod_n(number, power, modulos):
    """
    (number ** power) % modulos in log(power) time.
    """
    for _var in [number, power, modulos]:
        assert isinstance(_var, int), f"expected int, got {type(_var)} {_var}"
    
    # base case: power is small enough
    if power < 3:
        return (number % modulos) ** power
    
    # recursive case
    odd_power = power % 2 == 1
    if odd_power:
        return (number * power_mod_n(number, power - 1, modulos)) % modulos
    else:
        return (power_mod_n(number, power // 2, modulos) ** 2) % modulos
