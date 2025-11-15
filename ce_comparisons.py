"""
CE-Style Value Comparison Functions
Exact implementations from Cheat Engine's memscan.pas
"""

import struct

class CEComparisons:
    """Cheat Engine comparison logic for all data types"""
    
    @staticmethod
    def byte_changed(new_val: bytes, old_val: bytes) -> bool:
        """CE: pbyte(newvalue)^<>pbyte(oldvalue)^"""
        return new_val[0] != old_val[0]
    
    @staticmethod
    def byte_unchanged(new_val: bytes, old_val: bytes) -> bool:
        """CE: pbyte(newvalue)^=pbyte(oldvalue)^"""
        return new_val[0] == old_val[0]
    
    @staticmethod
    def byte_increased(new_val: bytes, old_val: bytes) -> bool:
        """CE: pbyte(newvalue)^>pbyte(oldvalue)^"""
        return new_val[0] > old_val[0]
    
    @staticmethod
    def byte_decreased(new_val: bytes, old_val: bytes) -> bool:
        """CE: pbyte(newvalue)^<pbyte(oldvalue)^"""
        return new_val[0] < old_val[0]
    
    @staticmethod
    def byte_increased_by(new_val: bytes, old_val: bytes, amount: int) -> bool:
        """CE: pbyte(newvalue)^=pbyte(oldvalue)^+byte(value)"""
        return new_val[0] == (old_val[0] + amount) & 0xFF
    
    @staticmethod
    def byte_decreased_by(new_val: bytes, old_val: bytes, amount: int) -> bool:
        """CE: pbyte(newvalue)^=pbyte(oldvalue)^-byte(value)"""
        return new_val[0] == (old_val[0] - amount) & 0xFF
    
    # Int32 (DWORD) comparisons
    @staticmethod
    def int32_changed(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdword(newvalue)^<>pdword(oldvalue)^"""
        return struct.unpack('<i', new_val)[0] != struct.unpack('<i', old_val)[0]
    
    @staticmethod
    def int32_unchanged(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdword(newvalue)^=pdword(oldvalue)^"""
        return struct.unpack('<i', new_val)[0] == struct.unpack('<i', old_val)[0]
    
    @staticmethod
    def int32_increased(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdword(newvalue)^>pdword(oldvalue)^"""
        return struct.unpack('<i', new_val)[0] > struct.unpack('<i', old_val)[0]
    
    @staticmethod
    def int32_decreased(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdword(newvalue)^<pdword(oldvalue)^"""
        return struct.unpack('<i', new_val)[0] < struct.unpack('<i', old_val)[0]
    
    @staticmethod
    def int32_increased_by(new_val: bytes, old_val: bytes, amount: int) -> bool:
        """CE: pdword(newvalue)^=pdword(oldvalue)^+dword(value)"""
        new = struct.unpack('<i', new_val)[0]
        old = struct.unpack('<i', old_val)[0]
        return new == old + amount
    
    @staticmethod
    def int32_decreased_by(new_val: bytes, old_val: bytes, amount: int) -> bool:
        """CE: pdword(newvalue)^=pdword(oldvalue)^-dword(value)"""
        new = struct.unpack('<i', new_val)[0]
        old = struct.unpack('<i', old_val)[0]
        return new == old - amount
    
    @staticmethod
    def int32_bigger_than(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdword(newvalue)^>pdword(oldvalue)^"""
        return struct.unpack('<i', new_val)[0] > struct.unpack('<i', old_val)[0]
    
    @staticmethod
    def int32_smaller_than(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdword(newvalue)^<pdword(oldvalue)^"""
        return struct.unpack('<i', new_val)[0] < struct.unpack('<i', old_val)[0]
    
    # Int64 (QWORD) comparisons
    @staticmethod
    def int64_changed(new_val: bytes, old_val: bytes) -> bool:
        """CE: pqword(newvalue)^<>pqword(oldvalue)^"""
        return struct.unpack('<q', new_val)[0] != struct.unpack('<q', old_val)[0]
    
    @staticmethod
    def int64_unchanged(new_val: bytes, old_val: bytes) -> bool:
        """CE: pqword(newvalue)^=pqword(oldvalue)^"""
        return struct.unpack('<q', new_val)[0] == struct.unpack('<q', old_val)[0]
    
    @staticmethod
    def int64_increased(new_val: bytes, old_val: bytes) -> bool:
        """CE: pqword(newvalue)^>pqword(oldvalue)^"""
        return struct.unpack('<q', new_val)[0] > struct.unpack('<q', old_val)[0]
    
    @staticmethod
    def int64_decreased(new_val: bytes, old_val: bytes) -> bool:
        """CE: pqword(newvalue)^<pqword(oldvalue)^"""
        return struct.unpack('<q', new_val)[0] < struct.unpack('<q', old_val)[0]
    
    @staticmethod
    def int64_increased_by(new_val: bytes, old_val: bytes, amount: int) -> bool:
        """CE: pqword(newvalue)^=pqword(oldvalue)^+qword(value)"""
        new = struct.unpack('<q', new_val)[0]
        old = struct.unpack('<q', old_val)[0]
        return new == old + amount
    
    @staticmethod
    def int64_decreased_by(new_val: bytes, old_val: bytes, amount: int) -> bool:
        """CE: pqword(newvalue)^=pqword(oldvalue)^-qword(value)"""
        new = struct.unpack('<q', new_val)[0]
        old = struct.unpack('<q', old_val)[0]
        return new == old - amount
    
    # Float (Single) comparisons
    @staticmethod
    def float_changed(new_val: bytes, old_val: bytes) -> bool:
        """CE: psingle(newvalue)^<>psingle(oldvalue)^"""
        return struct.unpack('<f', new_val)[0] != struct.unpack('<f', old_val)[0]
    
    @staticmethod
    def float_unchanged(new_val: bytes, old_val: bytes) -> bool:
        """CE: psingle(newvalue)^=psingle(oldvalue)^"""
        return struct.unpack('<f', new_val)[0] == struct.unpack('<f', old_val)[0]
    
    @staticmethod
    def float_increased(new_val: bytes, old_val: bytes) -> bool:
        """CE: psingle(newvalue)^>psingle(oldvalue)^"""
        return struct.unpack('<f', new_val)[0] > struct.unpack('<f', old_val)[0]
    
    @staticmethod
    def float_decreased(new_val: bytes, old_val: bytes) -> bool:
        """CE: psingle(newvalue)^<psingle(oldvalue)^"""
        return struct.unpack('<f', new_val)[0] < struct.unpack('<f', old_val)[0]
    
    @staticmethod
    def float_increased_by(new_val: bytes, old_val: bytes, amount: float) -> bool:
        """CE: psingle(newvalue)^=psingle(oldvalue)^+single(value)"""
        new = struct.unpack('<f', new_val)[0]
        old = struct.unpack('<f', old_val)[0]
        return abs((new - old) - amount) < 0.00001  # Float precision
    
    @staticmethod
    def float_decreased_by(new_val: bytes, old_val: bytes, amount: float) -> bool:
        """CE: psingle(newvalue)^=psingle(oldvalue)^-single(value)"""
        new = struct.unpack('<f', new_val)[0]
        old = struct.unpack('<f', old_val)[0]
        return abs((old - new) - amount) < 0.00001
    
    # Double comparisons
    @staticmethod
    def double_changed(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdouble(newvalue)^<>pdouble(oldvalue)^"""
        return struct.unpack('<d', new_val)[0] != struct.unpack('<d', old_val)[0]
    
    @staticmethod
    def double_unchanged(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdouble(newvalue)^=pdouble(oldvalue)^"""
        return struct.unpack('<d', new_val)[0] == struct.unpack('<d', old_val)[0]
    
    @staticmethod
    def double_increased(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdouble(newvalue)^>pdouble(oldvalue)^"""
        return struct.unpack('<d', new_val)[0] > struct.unpack('<d', old_val)[0]
    
    @staticmethod
    def double_decreased(new_val: bytes, old_val: bytes) -> bool:
        """CE: pdouble(newvalue)^<pdouble(oldvalue)^"""
        return struct.unpack('<d', new_val)[0] < struct.unpack('<d', old_val)[0]
    
    @staticmethod
    def double_increased_by(new_val: bytes, old_val: bytes, amount: float) -> bool:
        """CE: pdouble(newvalue)^=pdouble(oldvalue)^+double(value)"""
        new = struct.unpack('<d', new_val)[0]
        old = struct.unpack('<d', old_val)[0]
        return abs((new - old) - amount) < 0.0000000001  # Double precision
    
    @staticmethod
    def double_decreased_by(new_val: bytes, old_val: bytes, amount: float) -> bool:
        """CE: pdouble(newvalue)^=pdouble(oldvalue)^-double(value)"""
        new = struct.unpack('<d', new_val)[0]
        old = struct.unpack('<d', old_val)[0]
        return abs((old - new) - amount) < 0.0000000001
