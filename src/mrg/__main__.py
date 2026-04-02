from __future__ import annotations

import argparse
from pathlib import Path

from mrg._cleaner import Cleaner
from mrg._ansi_colors import Colors as C

DOT_UNDERSCORED = f"{C.BOLD}{C.UNDERLINE}._*{C.END}"

parser = argparse.ArgumentParser("MRG", usage="remove miscellaneous files produced by macOS")
# parser.add_argument("path", nargs="?", default=Path.cwd(), type=Path, help="path to remove miscellaneous files recursively (default: current working directory)")
parser.add_argument("path", type=Path, help="path to remove miscellaneous files recursively")
parser.add_argument("--all", action="store_true", help=f"clean selected directory; equivalent to {C.BLUE}{C.ITALIC}--ds-store --dot-underscored --bad-unicode{C.END}")
parser.add_argument("--ds-store", action="store_true", help=f"delete {C.BOLD}{C.UNDERLINE}.DS_Store{C.END} files")
parser.add_argument("--bad-unicode", action="store_true", help="normalize unicode characters to NFC")
parser.add_argument("--dot", action="store_true", help=f"delete {DOT_UNDERSCORED} files")
parser.add_argument("--dot-any-size", action="store_true", help=f"delete {DOT_UNDERSCORED} files even if it's not conventional size (implies {C.BLUE}{C.ITALIC}--dot{C.END})")
parser.add_argument("--dot-not-matching", action="store_true", help=f"delete {DOT_UNDERSCORED} files even if there's no corresponding native file (implies {C.BLUE}{C.ITALIC}--dot{C.END})")
parser.add_argument("--dot-all", action="store_true", help=f"delete all {DOT_UNDERSCORED} files; equivalent to {C.BLUE}{C.ITALIC}--dot-underscored-any-size --dot-underscored-not-matching{C.END}")
parser.add_argument("--enumerate", action="store_true", help="print every cleaned/scanned files")
parser.add_argument("--json", action="store_true", help="produce json report instead of text description")
parser.add_argument("--follow-symlinks", action="store_true", help="follow symlinks while traversing")
parser.add_argument("--version", action="version", version="0.1.1")


def main():
    args = parser.parse_args()
    all = args.all
    dot_all = args.dot_all
    cleaner = Cleaner(
        base_path=args.path,
        enumerate_cleaned=args.enumerate,
        remove_ds_store=all or args.ds_store,
        replace_bad_unicode=all or args.bad_unicode,
        remove_dot_underscored=all or dot_all or args.dot or args.dot_any_size or args.dot_not_matching,
        remove_dot_any_size=dot_all or args.dot_any_size,
        remove_dot_not_matching=dot_all or args.dot_not_matching,
        follow_symlinks=dot_all or args.follow_symlinks,
    )
    cleaner.clean()
    if args.json:
        import json

        report = cleaner.dictionary_report()
        print(json.dumps(report, ensure_ascii=False))
    else:
        cleaner.print_analyzed()


if __name__ == "__main__":
    main()
