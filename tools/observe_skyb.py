#!/usr/bin/env python3
"""
Observation tool. NOT part of the DSX reference implementation.

Walks the container framing of publicly distributed .skyb fixture files and
reports what is actually present in the bytes. Written from scratch to record
observable facts for the specification annex.
"""
import sys, os, struct, binascii

def walk(path):
    data = open(path, 'rb').read()
    n = len(data)
    out = []
    out.append(f"### {os.path.basename(path)}  ({n} bytes)")
    out.append(f"    head: {binascii.hexlify(data[:16]).decode()}")

    if data[:4] != b'skyb':
        out.append("    !! no 'skyb' marker")
        return "\n".join(out)

    p = 4
    version = data[p]; p += 1
    out.append(f"    version = {version}")

    if version >= 2:
        features = data[p]; p += 1
        out.append(f"    feature byte = 0x{features:02x} (bits: {features:08b})")
        if features & 0x01:
            crc = struct.unpack_from('<I', data, p)[0]; p += 4
            # verify over remainder
            calc = binascii.crc32(data[p:]) & 0xFFFFFFFF
            ok = "MATCH" if calc == crc else f"MISMATCH (calc {calc:08x})"
            out.append(f"    crc32 stored = {crc:08x}  over-remainder {ok}")

    out.append(f"    body starts at offset {p}")
    while p < n:
        if p + 3 > n:
            out.append(f"    !! truncated header at {p} ({n-p} bytes left)")
            break
        btype = data[p]
        blen = struct.unpack_from('<H', data, p + 1)[0]
        body = data[p + 3: p + 3 + blen]
        short = "TRUNCATED" if len(body) < blen else ""
        out.append(f"    @{p:5d}  type={btype}  len={blen:5d}  {short}"
                   f"  first={binascii.hexlify(body[:12]).decode()}")
        p += 3 + blen
        if btype == 0:
            out.append("    (type 0 encountered - possible terminator)")
    return "\n".join(out)

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    for f in sorted(os.listdir(d)):
        if f.endswith('.skyb'):
            print(walk(os.path.join(d, f)))
            print()
