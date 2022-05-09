import random
from .math import Factorizer, power_mod_n


class RSA:
    """
    RSA encryption.
    n = p * q where p, q are prime.
    c = (m ** e) % n
    m = (c ** d) % n
    """
    BUILTIN_FACTORIZER = Factorizer()
    
    def __init__(self, n, e, d):
        self.__class__.check_parameter(n, e, d)
        self.n, self.e, self.d = n, e, d
        
    @classmethod
    def from_pq(cls, p, q):
        fac = cls.BUILTIN_FACTORIZER
        assert isinstance(p, int) and p > 10, f"prime is too small: {p}"
        assert isinstance(q, int) and q > 10, f"prime is too small: {q}"
        assert len(fac.factorize(p)) == 1, f"{p} is not prime"
        assert len(fac.factorize(q)) == 1, f"{q} is not prime"
        
        totient = (p - 1) * (q - 1)
        factors = fac.factorize(totient + 1)
        assert len(factors) > 1, f"need at least 2 different factors, got {factors}"
        
        # auto-determine e and d with randomization
        factor_list = []
        for _k, _v in factors.items():
            factor_list.extend([_k] * _v)
        random.shuffle(factor_list)
        
        e, d = 1, 1
        while factor_list:
            if e <= d:
                e *= factor_list.pop()
            else:
                d *= factor_list.pop()
        
        n = p * q
        e, d = (e, d) if e >= d else (d, e)
        return cls(n, e, d)
    
    @classmethod
    def check_parameter(cls, n, e, d):
        factors = cls.BUILTIN_FACTORIZER.factorize(n)
        assert len(factors) == 2 and sum(factors.values()) == 2, f"invalid n {n}"
        p, q = factors.keys()
        totient = (p - 1) * (q - 1)
        assert e * d == totient + 1, "totient formula mismatch"
        assert e > 1 and d > 1, f"unexpected (e, d) pair: ({e}, {d})"
        
    @classmethod
    def given_digits(cls, num_digits, attempts=5):
        """
        Auto-create RSA object given the max number of digits to encrypt.
        """
        # sanity check: should support at least 10 digits for basic security
        assert isinstance(num_digits, int)
        num_digits = max(10, num_digits)
        
        # 1.1 * number cap > some prime > number cap
        bound = 11 * 10 ** (num_digits - 1)
        fac = cls.BUILTIN_FACTORIZER
        fac.factorize(bound)
        prime_range_length = 2 * num_digits ** 3
        assert prime_range_length < len(fac.list_primes), f"Too few primes: expected at least {prime_range_length}, got {len(fac.list_primes)}"
        prime_pool = fac.list_primes[-prime_range_length:]
        
        for _ in range(attempts):
            p, q = random.sample(prime_pool, 2)
            totient = (p - 1) * (q - 1)
            if len(fac.factorize(totient + 1)) < 2:
                continue
            return cls.from_pq(p, q)
        
        raise ValueError("ran out of attempts to construct RSA")
    
    def describe(self):
        return {"e": self.e, "d": self.d, "n": self.n}
    
    def encrypt(self, value):
        assert value < self.n, "Value is too large"
        return power_mod_n(value, self.e, self.n)
    
    def decrypt(self, value):
        return power_mod_n(value, self.d, self.n)

