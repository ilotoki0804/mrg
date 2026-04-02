import os
from pathlib import Path
from typing import Literal
from unicodedata import normalize, is_normalized

from mrg._ansi_colors import Colors as C


class Cleaner:
    def __init__(
        self,
        base_path: Path,
        enumerate_cleaned: bool,
        remove_ds_store: bool,
        replace_bad_unicode: bool,
        remove_dot_underscored: bool,
        remove_dot_any_size: bool,
        remove_dot_not_matching: bool,
        follow_symlinks: bool,
    ) -> None:
        self.base_path: Path = base_path
        self.enumerate_cleaned: bool = enumerate_cleaned
        self.remove_ds_store: bool = remove_ds_store
        self.replace_bad_unicode: bool = replace_bad_unicode
        self.remove_dot_underscored: bool = remove_dot_underscored
        self.remove_dot_any_size: bool = remove_dot_any_size
        self.remove_dot_not_matching: bool = remove_dot_not_matching
        self.follow_symlinks: bool = follow_symlinks
        self.is_cleaning: bool = (
            self.remove_ds_store
            or self.remove_dot_underscored
            or self.remove_dot_any_size
            or self.remove_dot_not_matching
            or self.replace_bad_unicode
        )
        self.enumerate_scanned: bool = self.enumerate_cleaned and not self.is_cleaning

    def clean(self) -> None:
        self._initialize_counters()
        abs_base_path = str(self.base_path.absolute())
        self.bad_unicode_base_path = not is_normalized("NFC", abs_base_path)
        if self.bad_unicode_base_path:
            if self.enumerate_cleaned or self.enumerate_scanned:
                print(f"{C.RED}{C.ITALIC}not normalized base path{C.END} {C.RED}{C.UNDERLINE}{C.BOLD}(won't be fixed automatically){C.END}{C.RED}{C.ITALIC}:{C.END} {self._path_repr(abs_base_path)}")

        for path, dirnames, filenames in self.base_path.walk(follow_symlinks=self.follow_symlinks, on_error=self._on_walk_error):
            self.scanned_files += len(filenames)
            self.scanned_dirs += len(dirnames)

            for i, dirname in enumerate(dirnames):
                if not is_normalized("NFC", dirname):
                    dirpath = path / dirname
                    if self.replace_bad_unicode:
                        if self.enumerate_cleaned:
                            print(f"{C.BLUE}{C.ITALIC}normalize directory name as NFC:{C.END} {self._path_repr(dirpath)}")
                        normalized_name = normalize("NFC", dirname)
                        os.rename(dirpath, path / normalized_name)
                        dirnames[i] = normalized_name
                    else:
                        if self.enumerate_scanned:
                            print(f"{C.RED}{C.ITALIC}not normalized directory:{C.END} {self._path_repr(path / dirname)}")
                    self.bad_unicode_dir += 1

            ds_store_found = False
            entries = set(filenames).union(dirnames)
            for filename in sorted(filenames):
                filepath = path / filename
                if not is_normalized("NFC", filename):
                    if self.replace_bad_unicode:
                        if self.enumerate_cleaned:
                            print(f"{C.BLUE}{C.ITALIC}normalize filename as NFC:{C.END} {self._path_repr(filepath)}")
                        normalized_name = normalize("NFC", filename)
                        normalized_path = path / normalized_name
                        os.rename(filepath, normalized_path)
                        filename = normalized_name
                        filepath = normalized_path
                    else:
                        if self.enumerate_scanned:
                            print(f"{C.RED}{C.ITALIC}not normalized path:{C.END} {self._path_repr(path / filename)}")
                    self.bad_unicode_file += 1

                if filename == ".DS_Store":
                    ds_store_found = True
                    continue

                prefix_removed = filename.removeprefix("._")
                if prefix_removed != filename:
                    corresponding_file = prefix_removed in entries
                    self.check_dot_underscored(filepath, corresponding_file)

            if ds_store_found:
                filepath = path / ".DS_Store"
                if self.remove_ds_store:
                    if self.enumerate_cleaned:
                        print(f"{C.BLUE}{C.ITALIC}remove .DS_Store:{C.END} {self._path_repr(filepath)}")
                    self._unlink(filepath)
                else:
                    if self.enumerate_scanned:
                        print(f"{C.PURPLE}{C.ITALIC}.DS_Store file:{C.END} {self._path_repr(filepath)}")
                self.ds_store += 1

    def check_dot_underscored(self, filepath: Path, corresponding_file: bool) -> None:
        size = filepath.stat().st_size
        is_conventional_size = size == 4096 or size == 176
        will_be_cleaned = (
            self.remove_dot_underscored
            and (is_conventional_size or self.remove_dot_any_size)
            and (corresponding_file or self.remove_dot_not_matching)
        )

        match corresponding_file, is_conventional_size:
            case True, True:
                file_type = "dot underscored"
                self.dot_underscored += 1
                faint = False
            case True, False:
                file_type = f"dot underscored ({size} bytes sized)"
                self.dot_any_size += 1
                faint = True
            case False, True:
                file_type = "dot underscored (no corresponding file)"
                self.dot_not_matching += 1
                faint = True
            case False, False:
                file_type = f"dot underscored (no corresponding file and {size} bytes sized)"
                self.dot_underscored_only += 1
                faint = True

        if will_be_cleaned:
            if self.enumerate_cleaned:
                print(f"{C.BLUE}{C.ITALIC}remove {file_type}:{C.END} {self._path_repr(filepath)}")
            self._unlink(filepath)
        else:
            if self.enumerate_scanned:
                if faint:
                    print(f"{C.FAINT}{C.ITALIC}{file_type}:{C.END} {C.FAINT}{self._path_repr(filepath)}{C.END}")
                else:
                    print(f"{C.PURPLE}{C.ITALIC}{file_type}:{C.END} {self._path_repr(filepath)}")

    def print_analyzed(self) -> None:
        cleaned_dot_underscores = (
            self.dot_underscored * self.remove_dot_underscored
            + self.dot_any_size * self.remove_dot_any_size
            + self.dot_not_matching * self.remove_dot_not_matching
            + self.dot_underscored_only * (self.remove_dot_any_size and self.remove_dot_not_matching)
        )
        cleaned_files = self.ds_store * self.remove_ds_store + cleaned_dot_underscores
        fixed_files = (
            self.bad_unicode_dir + self.bad_unicode_file
        ) * self.replace_bad_unicode
        cleaned_or_fixed_files = (
            cleaned_files + self.bad_unicode_file * self.replace_bad_unicode
        )
        fixed_directories = self.bad_unicode_dir * self.replace_bad_unicode
        scanned_entries = self.scanned_dirs + self.scanned_files

        G_BOLD = f"{C.GREEN}{C.BOLD}"
        B_BOLD = f"{C.BLUE}{C.BOLD}"
        P_BOLD = f"{C.PURPLE}{C.BOLD}"
        R_BOLD = f"{C.RED}{C.BOLD}"
        MRG = f"{C.BOLD}mrg{C.END}"
        DOT_UNDERSCORED = f"{C.BOLD}{C.UNDERLINE}._*{C.END}"
        DS_STORE = f"{C.BOLD}{C.UNDERLINE}.DS_Store{C.END}"

        def wrap(
            color: Literal["green", "blue", "purple", "red", "bold", "italic", "faint"],
            count: int | float,
            singular: str | None = None,
            plural: str | None = None,
            add_space: bool = True,
            percent: bool = False,
        ) -> str:
            match color:
                case "green":
                    WRAPPER = G_BOLD
                case "blue":
                    WRAPPER = B_BOLD
                case "purple":
                    WRAPPER = P_BOLD
                case "red":
                    WRAPPER = R_BOLD
                case "bold":
                    WRAPPER = C.BOLD
                case "italic":
                    WRAPPER = C.ITALIC
                case "faint":
                    WRAPPER = C.FAINT
                case _:
                    raise ValueError(f"unknown color: {color}")

            if percent:
                if count:
                    return f"{WRAPPER}{count:.02%}{C.END}"
                else:
                    return f"{C.FAINT}{C.ITALIC}{count:.02%}{C.END}"

            if count == 1:
                following = f"{' ' * add_space}{singular}" if singular else ""
            else:
                following = f"{' ' * add_space}{plural}" if plural else ""

            if count:
                return f"{WRAPPER}{count}{C.END}{following}"
            else:
                return f"{C.FAINT}{C.ITALIC}{count}{C.END}{following}"

        total_scan_findings = (
            self.ds_store
            + self.bad_unicode_dir
            + self.bad_unicode_file
            + self.dot_underscored
            + self.dot_any_size
            + self.dot_not_matching
            + self.dot_underscored_only
        )

        # print an empty line if any enumeration has been occurred
        if (
            self.enumerate_cleaned
            and (cleaned_files + fixed_files)
            or self.enumerate_scanned
            and (total_scan_findings or self.bad_unicode_base_path)
        ):
            print()

        if cleaned_files + fixed_files:
            print(f'{MRG} have scanned {wrap("green", scanned_entries, "entry", "entries")} ({wrap("green", self.scanned_files, "file", "files")} and {wrap("green", self.scanned_dirs, "directory", "directories")}) and cleaned or fixed {wrap("blue", cleaned_files + fixed_files, "entry", "entries")} ({wrap("blue", (cleaned_files + fixed_files) / (scanned_entries or 1), percent=True)})')
        else:
            print(f'{MRG} have scanned {wrap("green", scanned_entries, "entry", "entries")} ({wrap("green", self.scanned_files, "file", "files")} and {wrap("green", self.scanned_dirs, "directory", "directories")}) without making any changes')

        if total_scan_findings or self.bad_unicode_base_path or self.scan_failed_dirs:
            print(f"{C.BOLD}{C.UNDERLINE}{C.ITALIC}Analysis:{C.END}")
        else:
            print(f"{C.ITALIC}Nothing{C.END} found. What a clean directory!")
        if self.scan_failed_dirs:
            print(f'    {R_BOLD}Failed to scan{C.END} {wrap('red', self.scan_failed_dirs, f"{R_BOLD}directory{C.END}", f"{R_BOLD}directories{C.END}")}')
        if cleaned_files + fixed_files:
            print(f'    {wrap("blue", cleaned_or_fixed_files, "file", "files")} ({wrap("blue", cleaned_or_fixed_files / (self.scanned_files or 1), percent=True)}) and {wrap("blue", fixed_directories, "directory", "directories")} ({wrap("blue", fixed_directories / (self.scanned_dirs or 1), percent=True)}) cleaned or fixed')
        if self.ds_store:
            if self.remove_ds_store:
                print(f'    {wrap("blue", self.ds_store, f"{DS_STORE} file has been", f"{DS_STORE} files have been")} {B_BOLD}cleaned{C.END} ({wrap("bold", self.ds_store / (self.scanned_files or 1), percent=True)})')
            else:
                print(f'    {wrap("bold", self.ds_store, f"{DS_STORE} file has been", f"{DS_STORE} files have been")} {P_BOLD}found{C.END} ({wrap("bold", self.ds_store / (self.scanned_files or 1), percent=True)})')
        if self.bad_unicode_base_path:
            print(f'''    base path "{C.BOLD}{C.UNDERLINE}{self.base_path.absolute()}{C.END}" is {C.RED}not normalized{C.END} (won't be fixed automatically)''')
        if bad_unicode := self.bad_unicode_dir + self.bad_unicode_file:
            if self.replace_bad_unicode:
                print(f'    {wrap("blue", bad_unicode, "entry", "entries")} ({wrap("blue", self.bad_unicode_dir, "directory", "directories")} and {wrap("blue", self.bad_unicode_file, "file", "files")}, {wrap("blue", bad_unicode / scanned_entries, percent=True)}) unicode normalized')
            else:
                print(f'    {wrap("bold", bad_unicode, "not unicode normalized entry", "not unicode normalized entries")} ({wrap("bold", bad_unicode / scanned_entries, percent=True)}, {wrap("bold", self.bad_unicode_dir, "directory", "directories")} and {wrap("bold", self.bad_unicode_file, "file", "files")}) {P_BOLD}found{C.END}')
        if self.dot_underscored + self.dot_any_size + self.dot_not_matching + self.dot_underscored_only:
            if self.remove_dot_underscored:
                print(f'    {wrap("blue", cleaned_dot_underscores, f"{DOT_UNDERSCORED} file has been", f"{DOT_UNDERSCORED} files have been")} {B_BOLD}cleaned{C.END} ({wrap("blue", cleaned_dot_underscores / (self.scanned_files or 1), percent=True)}) in total')
            else:
                print(f'    {wrap("bold", self.dot_underscored, f"{DOT_UNDERSCORED} file has been", f"{DOT_UNDERSCORED} files have been")} {P_BOLD}found{C.END} ({wrap("bold", self.dot_underscored / (self.scanned_files or 1), percent=True)})')

            if self.dot_any_size + self.dot_not_matching + self.dot_underscored_only:
                but_not_cleaned = " but not cleaned" * (self.remove_dot_underscored or self.remove_dot_any_size or self.remove_dot_not_matching)
                print(f"    {C.ITALIC}in detail:{C.END}")
                if self.remove_dot_underscored:
                    print(f'        {wrap("blue", self.dot_underscored, f"{DOT_UNDERSCORED} file", f"{DOT_UNDERSCORED} files")} {B_BOLD}cleaned{C.END}')
                else:
                    print(f'        {wrap("bold", self.dot_underscored, f"{DOT_UNDERSCORED} file", f"{DOT_UNDERSCORED} files")} {P_BOLD}found{C.END}{but_not_cleaned}')

                if self.dot_any_size:
                    if self.remove_dot_any_size:
                        file = f"{C.RED}{C.ITALIC}not conventionally sized{C.END} {DOT_UNDERSCORED} file"
                        print(f'        {wrap("blue", self.dot_any_size, file, file + "s")} {B_BOLD}cleaned{C.END}')
                    else:
                        file = f"{C.RED}{C.ITALIC}{C.UNDERLINE}{C.FAINT}not conventionally sized{C.END} {C.FAINT}._* file"
                        print(f'        {wrap("faint", self.dot_any_size, file, file + "s")} found{but_not_cleaned}{C.END}')

                if self.dot_not_matching:
                    if self.remove_dot_not_matching:
                        file = f"{C.RED}{C.ITALIC}not matching{C.END} {DOT_UNDERSCORED} file"
                        print(f'        {wrap("blue", self.dot_not_matching, file, file + "s")} {B_BOLD}cleaned{C.END}')
                    else:
                        file = f"{C.RED}{C.ITALIC}{C.UNDERLINE}{C.FAINT}not matching{C.END} {C.FAINT}._* file"
                        print(f'        {wrap("faint", self.dot_not_matching, file, file + "s")} found{but_not_cleaned}{C.END}')

                if self.dot_underscored_only:
                    if self.remove_dot_not_matching:
                        file = f"{C.RED}{C.ITALIC}not matching and not conventionally sized{C.END} {DOT_UNDERSCORED} file"
                        print(f'        {wrap("blue", self.dot_underscored_only, file, file + "s")} {B_BOLD}cleaned{C.END}')
                    else:
                        file = f"{C.RED}{C.ITALIC}{C.UNDERLINE}{C.FAINT}not matching and not conventionally sized{C.END} {C.FAINT}._* file"
                        print(f'        {wrap("faint", self.dot_underscored_only, file, file + "s")} found{but_not_cleaned}{C.END}')

    def dictionary_report(self) -> dict:
        return dict(
            scanned_files=self.scanned_files,
            ds_store=self.ds_store,
            bad_unicode_base_path=self.bad_unicode_base_path,
            bad_unicode_dir=self.bad_unicode_dir,
            bad_unicode_file=self.bad_unicode_file,
            dot_underscored=self.dot_underscored,
            dot_any_size=self.dot_any_size,
            dot_not_matching=self.dot_not_matching,
            dot_underscored_only=self.dot_underscored_only,
            ds_store_fixed=self.remove_ds_store,
            bad_unicode_fixed=self.replace_bad_unicode,
            dot_underscored_fixed=self.remove_dot_underscored,
            dot_any_size_fixed=self.remove_dot_any_size,
            dot_not_matching_fixed=self.remove_dot_not_matching,
        )

    def _initialize_counters(self) -> None:
        self.scanned_files: int = 0
        self.scanned_dirs: int = 0
        self.ds_store: int = 0
        self.bad_unicode_base_path: bool = False
        self.bad_unicode_dir: int = 0
        self.bad_unicode_file: int = 0
        self.dot_underscored: int = 0
        self.dot_any_size: int = 0
        self.dot_not_matching: int = 0
        self.dot_underscored_only: int = 0
        self.scan_failed_dirs: int = 0

    @staticmethod
    def _unlink(file: Path):
        os.unlink(normalize("NFC", str(file)))

    @staticmethod
    def _path_repr(path: Path | str) -> str:
        return f"{C.UNDERLINE}{C.BOLD}{path}{C.END}"

    def _on_walk_error(self, error: OSError) -> None:
        path = Path(error.filename)
        if error_repr := str(error):
            print(f"{C.RED}{C.ITALIC}failed to access directory {C.END}{C.RED}({C.BOLD}{type(error).__name__}{C.END}{C.RED}: {error_repr}{C.RED}):{C.END} {self._path_repr(path)}")
        else:
            print(f"{C.RED}{C.ITALIC}failed to access directory {C.END}{C.RED}({C.BOLD}{type(error).__name__}{C.END}{C.RED}):{C.END} {self._path_repr(path)}")
        self.scan_failed_dirs += 1
