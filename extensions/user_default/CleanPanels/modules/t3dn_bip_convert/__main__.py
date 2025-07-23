from argparse import ArgumentParser
from .convert import convert_file

if __name__ == "__main__":
    parser = ArgumentParser(description="convert between BIP and other formats")
    parser.add_argument("src", type=str, help="input path")
    parser.add_argument("dst", type=str, nargs="?", help="output path")

    args = parser.parse_args()
    convert_file(args.src, args.dst)

# python -m t3dn_bip_converter src.png dst.bip
