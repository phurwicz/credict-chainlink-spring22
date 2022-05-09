"""
Watermarks to help verify if predictions are possibly original to an Ether address.
"""
import random


class AddressBasedWatermarker:
    def __init__(self, address_hex_str):
        """
        Store address and compute indices that can be used for watermark.
        """
        addr_str = str(int(address_hex_str, 16))
        self.indices = [i for i in range(len(addr_str)) if addr_str[i] != "0"]
        self.address_base10_str = addr_str
    
    def create(self, watermark_length=10):
        """
        Sample non-zero digits from the address to create a substring.
        """
        assert watermark_length < len(self.indices), f"max {len(self.indices)} digits"
        
        indices = sorted(random.sample(self.indices, watermark_length))
        return int("".join([self.address_base10_str[i] for i in indices]))

    def verify(self, watermark):
        """
        Verify a watermark which should be a substring of the stored address in base10.
        """
        watermark_str = str(watermark)
        i, j = 0, 0
        while i < len(watermark_str):
            while watermark_str[i] != self.address_base10_str[j]:
                j += 1
                if j >= len(self.address_base10_str):
                    return False
            i += 1
        return True
    
    def extract(self, marked_value):
        """
        Extract watermark and unmarked value without verification.
        """
        pieces = str(marked_value).split("0")
        watermark = pieces[0]
        value = "0".join(pieces[1:])
        return watermark, value