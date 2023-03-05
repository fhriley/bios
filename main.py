import argparse
import re
import struct
import sys
from dataclasses import dataclass, fields
from pathlib import Path


@dataclass
class CpuSetup:
    revision: int = 0
    cpu_ratio: int = 0
    cpu_default_ratio: int = 0
    cpu_ratio_override: int = 0
    peci: int = 0
    hyper_threading: int = 0
    active_core_count: int = 0
    bist_on_reset: int = 0
    jtag_c10_power_gate_disable: int = 0
    enable_gv: int = 0
    race_to_halt: int = 0
    enable_hwp: int = 0


cpu_setup_format = '>12B'


def main(args):
    path = Path(args.filename)
    if not path.is_file():
        print(f'"{args.filename}" is not a file', file=sys.stderr)
        return 1

    out_path = path.parent / f'{path.stem}_hwp{args.enable_disable}{path.suffix}'
    if not args.force and out_path.exists():
        print(f'"{out_path}" already exists', file=sys.stderr)
        return 1

    with open(path, 'rb') as in_file:
        data = bytearray(in_file.read())

    pattern = b'CpuSetup\0'
    offsets = [m.start() + len(pattern) for m in re.finditer(pattern, data)]

    for offset in offsets:
        vals = struct.unpack_from(cpu_setup_format, data, offset)
        cpu_setup = CpuSetup(*vals)
        cpu_setup.enable_hwp = args.enable_disable
        new_vals = [getattr(cpu_setup, field.name) for field in fields(cpu_setup)]
        struct.pack_into(cpu_setup_format, data, offset, *new_vals)

    with open(out_path, 'wb') as out_file:
        out_file.write(data)

    print(f'Wrote "{out_path}"')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=sys.argv[0], description='Enable/disable HWP in an aptio V BIOS')
    parser.add_argument('filename', help='the binary BIOS file')
    parser.add_argument('enable_disable', type=int, choices=[1, 0], help='1 to enable, 0 to disable')
    parser.add_argument('-f', '--force', action='store_true', help='write the output file even if it already exists')
    pargs = parser.parse_args()

    raise SystemExit(main(pargs))
