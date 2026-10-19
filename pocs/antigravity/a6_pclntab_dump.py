#!/usr/bin/env python3
"""
a6_pclntab_dump.py — Parse the Go pclntab (function table) from a stripped Go
ELF binary WITHOUT disassembly. Cheap table parse only.

Targets Go >= 1.20 (magic 0xfffffff1). Validates candidates by header sanity
and cross-checks textStart against the ELF .text section VMA.

Usage: python3 a6_pclntab_dump.py /home/hatch/.local/bin/agy [--tsv out.tsv]

Memory: mmaps the file, no full read.
"""
import mmap
import struct
import sys
import os

MAGIC_GO120 = 0xFFFFFFF1

# ---- go1.28-internal (Google) pclntab layout, reverse-engineered ----
# pclntab @ file offset == VMA (sections not relocated in file).
# Header (72 bytes):
#   +0  magic u32 = 0xfffffff1
#   +4  pad1,pad2,minLC,ptrSize (u8 x4) -> expect 0,0,1,8
#   +8  nfunc i64
#   +16 nfiles u64
#   +24 u64 = 0  (textStart field absent/zero in this toolchain!)
#   +32 funcnameOff u64 (offset from pclntab base to func name strings)
#   +40 cuOff u64, +48 filetabOff u64, +56 pctabOff u64, +64 pclnOff u64
# functab array at base+pclnOff: nfunc entries of (entryOff u32, funcOff u32).
#   funcOff is relative to (base+pclnOff) -- NOT to pclntab base.
#   entryOff is relative to GO_TEXT_BASE (below), NOT an absolute address.
# func struct at (base+pclnOff+funcOff): entryOff u32 @+0, nameOff i32 @+4.
#   name = C string at (base+funcnameOff+nameOff).
#
# GO_TEXT_BASE: calibrated empirically (textStart==0 in header).
#   Method: histogram of Go stack-check prologue bytes 49 3b 66 10
#   (cmp rsp,[r14+0x10]) over .text -> Go-dense [0x61d4000..~0x9355820];
#   first hit at 0x61d4300, preceded by C code + INT3 padding.
#   functab[0] (entryOff=0) = internal/abi.(*RegArgs).Dump lands exactly
#   at 0x61d4300. Cross-check: T+maxEntryOff(0x3181520)=0x9355820 sits at
#   the end of the Go-dense region (C libm code resumes at 0x94bxxxx).
GO_TEXT_BASE = 0x61D4300

# ELF section header parse for .text VMA cross-check (kept for reference;
# unused for address computation since Go text != .text start here).
def get_text_vma(path):
    with open(path, "rb") as f:
        e = f.read(64)
        if e[:4] != b"\x7fELF":
            raise ValueError("not ELF")
        shoff = struct.unpack("<Q", e[0x28:0x30])[0]
        shentsize = struct.unpack("<H", e[0x3A:0x3C])[0]
        shnum = struct.unpack("<H", e[0x30:0x32])[0]
        shstrndx = struct.unpack("<H", e[0x32:0x34])[0]
        f.seek(shoff + shstrndx * shentsize)
        strtab = f.read(shentsize)
        stroff = struct.unpack("<Q", strtab[0x18:0x20])[0]
        f.seek(stroff)
        names = f.read(1 << 20)
        for i in range(shnum):
            f.seek(shoff + i * shentsize)
            sh = f.read(shentsize)
            name_off = struct.unpack("<I", sh[0:4])[0]
            name = names[name_off:].split(b"\x00", 1)[0].decode()
            if name == ".text":
                return struct.unpack("<Q", sh[0x10:0x18])[0]
    return None


def read_cstr(mm, off, limit=512):
    end = mm.find(b"\x00", off, off + limit)
    if end < 0:
        return None
    try:
        s = mm[off:end].decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not all(32 <= ord(c) < 127 or c in "\t" for c in s):
        return None
    return s


def try_parse(mm, base):
    """Try to parse a pclntab at offset `base`. Returns dict or None."""
    if base + 72 > len(mm):
        return None
    magic = struct.unpack_from("<I", mm, base)[0]
    if magic != MAGIC_GO120:
        return None
    pad1, pad2, minLC, ptrSize = struct.unpack_from("BBBB", mm, base + 4)
    (nfunc,) = struct.unpack_from("<q", mm, base + 8)
    (nfiles,) = struct.unpack_from("<Q", mm, base + 16)
    funcnameOff = struct.unpack_from("<Q", mm, base + 32)[0]
    pclnOff = struct.unpack_from("<Q", mm, base + 64)[0]
    # sanity
    if not (100 <= nfunc <= 5_000_000):
        return None
    if not (0 <= nfiles <= 1_000_000):
        return None
    if ptrSize != 8 or minLC not in (1, 2):
        return None
    if funcnameOff == 0 or pclnOff == 0:
        return None
    if base + funcnameOff >= len(mm) or base + pclnOff >= len(mm):
        return None
    # validate: funcnametab must start with plausible Go symbol strings
    head = mm[base + funcnameOff: base + funcnameOff + 64]
    if b"\x00" not in head:
        return None
    # validate: functab[0] must resolve through pcln-relative funcOff
    anchor = base + pclnOff
    f0off = struct.unpack_from("<I", mm, anchor + 4)[0]
    fstruct = anchor + f0off
    if fstruct + 16 > len(mm) or f0off > 0x4000000:
        return None
    nameOff = struct.unpack_from("<i", mm, fstruct + 4)[0]
    if nameOff < 0 or nameOff > 0x4000000:
        return None
    name = read_cstr(mm, base + funcnameOff + nameOff)
    if not name or len(name) < 2:
        return None
    # probe a middle function too
    mid = nfunc // 2
    fmid_off = struct.unpack_from("<I", mm, anchor + mid * 8 + 4)[0]
    fms = anchor + fmid_off
    if fms + 16 > len(mm) or fmid_off > 0x4000000:
        return None
    nameOff2 = struct.unpack_from("<i", mm, fms + 4)[0]
    name2 = read_cstr(mm, base + funcnameOff + nameOff2) if 0 <= nameOff2 < 0x4000000 else None
    if not name2:
        return None
    return {
        "base": base, "nfunc": nfunc, "nfiles": nfiles,
        "funcnameOff": funcnameOff, "pclnOff": pclnOff,
        "probe0": name, "probemid": name2,
    }


def dump(mm, info):
    base, nfunc = info["base"], info["nfunc"]
    anchor = base + info["pclnOff"]          # functab lives here; funcOff relative to it
    nametab = base + info["funcnameOff"]
    out = []
    for i in range(nfunc):
        entry = struct.unpack_from("<I", mm, anchor + i * 8)[0]
        fstruct = anchor + struct.unpack_from("<I", mm, anchor + i * 8 + 4)[0]
        nameOff = struct.unpack_from("<i", mm, fstruct + 4)[0]
        name = read_cstr(mm, nametab + nameOff) if nameOff >= 0 else None
        out.append((GO_TEXT_BASE + entry, name or "<unnamed:%d>" % i))
    return out


def pkg_of(name):
    # strip receiver: "pkg.(*T).M" -> pkg
    # package path = everything before the last '.' that isn't inside parens/brackets
    depth = 0
    cut = -1
    for i in range(len(name) - 1, -1, -1):
        c = name[i]
        if c in ")]":
            depth += 1
        elif c in "([":
            depth -= 1
        elif c == "." and depth == 0:
            cut = i
            break
    if cut <= 0:
        return "<nopkg>"
    return name[:cut]


def main():
    path = sys.argv[1]
    tsv = sys.argv[2] if len(sys.argv) > 2 else None
    size = os.path.getsize(path)
    print(f"file: {path} ({size/1e6:.1f} MB)", flush=True)

    text_vma = get_text_vma(path)
    print(f"ELF .text VMA: {hex(text_vma) if text_vma else 'N/A'}", flush=True)

    with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        magic_bytes = struct.pack("<I", MAGIC_GO120)
        print("scanning for pclntab magic 0xfffffff1 ...", flush=True)
        cands = []
        off = 0
        while True:
            off = mm.find(magic_bytes, off)
            if off < 0:
                break
            info = try_parse(mm, off)
            if info:
                cands.append(info)
                print(f"  candidate @ {hex(off)}: nfunc={info['nfunc']} "
                      f"probe={info['probe0']!r}", flush=True)
            off += 4
        if not cands:
            print("NO VALID PCLNTAB FOUND", flush=True)
            return 1
        info = max(cands, key=lambda c: c["nfunc"])
        print(f"selected pclntab @ {hex(info['base'])} "
              f"(nfunc={info['nfunc']}, nfiles={info['nfiles']})", flush=True)
        print(f"GO_TEXT_BASE={hex(GO_TEXT_BASE)} (empirical; header textStart==0)",
              flush=True)
        print("dumping function table ...", flush=True)
        funcs = dump(mm, info)

    print(f"TOTAL FUNCTIONS: {len(funcs)}", flush=True)
    pkgs = {}
    for addr, name in funcs:
        p = pkg_of(name)
        pkgs[p] = pkgs.get(p, 0) + 1
    top = sorted(pkgs.items(), key=lambda kv: -kv[1])[:30]
    print("TOP 30 PACKAGES BY FUNCTION COUNT:", flush=True)
    for p, c in top:
        print(f"  {c:6d}  {p}", flush=True)
    print(f"distinct packages: {len(pkgs)}", flush=True)
    unnamed = sum(1 for _, n in funcs if n.startswith("<unnamed"))
    print(f"unnamed entries: {unnamed}", flush=True)

    if tsv:
        with open(tsv, "w") as f:
            f.write("address\tname\n")
            for addr, name in funcs:
                f.write(f"{addr:#x}\t{name}\n")
        print(f"wrote {tsv}", flush=True)

    # integration-value keyword hits for targeted disassembly
    keys = ["telemetry", "usage", "flag", "grpc", "rpc.", "auth", "token",
            "config", "command", "main.main", "version", "update", "oauth"]
    print("KEYWORD HITS (integration value):", flush=True)
    for k in keys:
        hits = [(a, n) for a, n in funcs if k.lower() in n.lower()]
        print(f"  [{k}] {len(hits)} hits", flush=True)
        for a, n in hits[:8]:
            print(f"      {a:#x} {n}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
