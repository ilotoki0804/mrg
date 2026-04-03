from dataclasses import dataclass
import os
from pathlib import Path
from typing import Literal
from unicodedata import normalize, is_normalized

from mrg._ansi_colors import Colors as C

G_BOLD = f"{C.GREEN}{C.BOLD}"
B_BOLD = f"{C.BLUE}{C.BOLD}"
P_BOLD = f"{C.PURPLE}{C.BOLD}"
R_BOLD = f"{C.RED}{C.BOLD}"
MRG = f"{C.BOLD}mrg{C.END}"
DOT_UNDERSCORED = f"{C.BOLD}{C.UNDERLINE}._*{C.END}"
DS_STORE = f"{C.BOLD}{C.UNDERLINE}.DS_Store{C.END}"


@dataclass
class CleanStatus:
    cleaned: int = 0
    clean_failed: int = 0
    scanned: int = 0
    fix: bool = False

    def as_dict(self) -> dict:
        return dict(
            cleaned=self.cleaned,
            clean_failed=self.clean_failed,
            scanned=self.scanned,
            fix=self.fix,
        )

    @property
    def total_entries(self) -> int:
        return self.cleaned + self.clean_failed + self.scanned


class Cleaner:
    def __init__(
        self,
        base_path: Path,
        enumerate_cleaned: bool,
        enumerate_error: bool,
        remove_ds_store: bool,
        replace_bad_unicode: bool,
        remove_dot_underscored: bool,
        remove_dot_any_size: bool,
        remove_dot_not_matching: bool,
        follow_symlinks: bool,
    ) -> None:
        self.base_path: Path = base_path
        self.enumerate_cleaned: bool = enumerate_cleaned
        self.enumerate_error: bool = enumerate_error
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
            self._enumerate(
                f"{C.RED}{C.ITALIC}not normalized base path{C.END} {C.RED}{C.UNDERLINE}{C.BOLD}(won't be fixed automatically){C.END}{C.RED}{C.ITALIC}",
                abs_base_path,
                self.enumerate_cleaned or self.enumerate_scanned,
            )

        for path, dirnames, filenames in self.base_path.walk(follow_symlinks=self.follow_symlinks, on_error=self._on_walk_error):
            self.scanned_files += len(filenames)
            self.scanned_dirs += len(dirnames)

            for i, dirname in enumerate(dirnames):
                if not is_normalized("NFC", dirname):
                    dirpath = path / dirname
                    if self.replace_bad_unicode:
                        normalized_name = normalize("NFC", dirname)
                        try:
                            os.rename(dirpath, path / normalized_name)
                        except OSError as error:
                            self.bad_unicode_dir.clean_failed += 1
                            self._print_error("failed to normalize a file as NFC", path, error)
                        else:
                            self.bad_unicode_dir.cleaned += 1
                            self._enumerate(f"{C.BLUE}{C.ITALIC}normalize a directory as NFC", dirpath, self.enumerate_cleaned)
                        dirnames[i] = normalized_name
                    else:
                        self._enumerate(f"{C.RED}{C.ITALIC}not normalized directory", path / dirname, self.enumerate_scanned)
                        self.bad_unicode_dir.scanned += 1

            ds_store_found = False
            entries = set(filenames).union(dirnames)
            for filename in sorted(filenames):
                filepath = path / filename
                if not is_normalized("NFC", filename):
                    if self.replace_bad_unicode:
                        self._enumerate(f"{C.BLUE}{C.ITALIC}normalize a file as NFC", filepath, self.enumerate_cleaned)
                        normalized_name = normalize("NFC", filename)
                        normalized_path = path / normalized_name
                        try:
                            os.rename(filepath, normalized_path)
                        except OSError as error:
                            self.bad_unicode_file.clean_failed += 1
                            self._print_error("failed to normalize a file as NFC", path, error)
                        else:
                            self.bad_unicode_file.cleaned += 1
                            self._enumerate(f"{C.BLUE}{C.ITALIC}normalize a file as NFC", normalized_path, self.enumerate_cleaned)
                        filename = normalized_name
                        filepath = normalized_path
                    else:
                        self.bad_unicode_file.scanned += 1
                        self._enumerate(f"{C.BLUE}{C.ITALIC}not normalized path", filepath, self.enumerate_scanned)

                if filename == ".DS_Store":
                    ds_store_found = True
                    continue

                dot_underscore_removed = filename.removeprefix("._")
                if dot_underscore_removed != filename:
                    corresponding_file = dot_underscore_removed in entries
                    self.check_dot_underscored(filepath, corresponding_file)

            if ds_store_found:
                filepath = path / ".DS_Store"
                if self.remove_ds_store:
                    try:
                       self._unlink(filepath)
                    except OSError as error:
                        self.ds_store.clean_failed += 1
                        self._print_error(f"failed to unlink {DS_STORE}", path, error)
                    else:
                        self.ds_store.cleaned += 1
                        self._enumerate(f"{C.BLUE}{C.ITALIC}remove {DS_STORE}{C.BLUE}{C.ITALIC}", filepath, self.enumerate_cleaned)

                else:
                    self.ds_store.scanned += 1
                    self._enumerate(f"{C.PURPLE}{C.ITALIC}{DS_STORE}{C.PURPLE}{C.ITALIC} file", filepath, self.enumerate_scanned)

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
                status = self.dot_underscored
                faint = False
            case True, False:
                file_type = f"dot underscored ({size} bytes sized)"
                status = self.dot_any_size
                faint = True
            case False, True:
                file_type = "dot underscored (no corresponding file)"
                status = self.dot_not_matching
                faint = True
            case False, False:
                file_type = f"dot underscored (no corresponding file and {size} bytes sized)"
                status = self.dot_underscored_only
                faint = True

        if will_be_cleaned:
            try:
                self._unlink(filepath)
            except OSError as error:
                status.clean_failed += 1
                self._print_error(f"failed to unlink {file_type}", filepath, error)
            else:
                status.cleaned += 1
                self._enumerate(f"{C.BLUE}{C.ITALIC}remove {file_type}", filepath, self.enumerate_cleaned)

        else:
            status.scanned += 1
            if self.enumerate_scanned:
                if faint:
                    print(f"{C.FAINT}{C.ITALIC}{file_type}:{C.END} {C.FAINT}{self._path_repr(filepath)}{C.END}")
                else:
                    print(f"{C.PURPLE}{C.ITALIC}{file_type}:{C.END} {self._path_repr(filepath)}")

    def print_analyzed(self) -> None:
        cleaned_dot_underscores = (
            self.dot_underscored.cleaned
            + self.dot_any_size.cleaned
            + self.dot_not_matching.cleaned
            + self.dot_underscored_only.cleaned
        )
        cleaned_files = self.ds_store.cleaned + cleaned_dot_underscores
        fixed_files = self.bad_unicode_dir.cleaned + self.bad_unicode_file.cleaned
        cleaned_or_fixed_files = cleaned_files + self.bad_unicode_file.cleaned
        fixed_directories = self.bad_unicode_dir.cleaned
        total_scan_findings = (
            self.ds_store.total_entries
            + self.bad_unicode_dir.total_entries
            + self.bad_unicode_file.total_entries
            + self.dot_underscored.total_entries
            + self.dot_any_size.total_entries
            + self.dot_not_matching.total_entries
            + self.dot_underscored_only.total_entries
        )

        # print an empty line if any enumeration has been occurred
        if (
            self.enumerate_cleaned
            and (cleaned_files + fixed_files)
            or self.enumerate_scanned
            and (total_scan_findings or self.bad_unicode_base_path)
        ):
            print()

        if self.scan_failed_dirs == 1 and self.scanned_dirs == -1:
            print(f'{C.RED}{C.BOLD}Failed to access base directory{C.END}')
            return

        if cleaned_or_fixed_files + fixed_directories:
            fix_message = f'and {B_BOLD}cleaned/normalized{C.END} {self._entry_analysis("bold", fixed_directories, cleaned_or_fixed_files)}'
        else:
            fix_message = 'without making any changes'
        if self.scanned_dirs + self.scanned_files:
            print(f'{MRG} have scanned {self._entry_analysis("green", self.scanned_dirs, self.scanned_files, percent=False)} {fix_message}')
        else:
            print(f'{C.ITALIC}Given directory is empty.{C.END}')

        if total_scan_findings or self.bad_unicode_base_path or self.scan_failed_dirs:
            print(f"{C.BOLD}{C.UNDERLINE}{C.ITALIC}Analysis:{C.END}")
        else:
            print(f"{C.GREEN}{C.ITALIC}Nothing{C.END} {C.GREEN}found. What a clean directory!{C.END}")
        if self.scan_failed_dirs:
            print(f'    {R_BOLD}Failed to scan{C.END} {self._wrap('red', self.scan_failed_dirs, f"{R_BOLD}directory{C.END}", f"{R_BOLD}directories{C.END}")}')
        if self.bad_unicode_base_path:
            print(f'    base path "{C.BOLD}{C.UNDERLINE}{self.base_path.absolute()}{C.END}" is {C.RED}not normalized{C.END} (won\'t be fixed automatically)')

        if self.bad_unicode_dir.cleaned + self.bad_unicode_file.cleaned:
            print(f'    {B_BOLD}Normalized{C.END} {self._entry_analysis("bold", self.bad_unicode_dir.cleaned, self.bad_unicode_file.cleaned, insert_before_percent="to NFC")}')
        if self.bad_unicode_dir.clean_failed + self.bad_unicode_file.clean_failed:
            print(f'    {R_BOLD}Failed to clean{C.END} {self._entry_analysis("bold", self.bad_unicode_dir.clean_failed, self.bad_unicode_file.clean_failed)} to NFC')
        if self.bad_unicode_dir.scanned + self.bad_unicode_file.scanned:
            print(f'    {P_BOLD}Found{C.END} {self._entry_analysis("bold", self.bad_unicode_dir.scanned, self.bad_unicode_file.scanned, insert="not NFC normalized")}')

        if cleaned := self.ds_store.cleaned:
            print(f'    {B_BOLD}Cleaned{C.END} {self._entry_analysis("bold", 0, cleaned, insert=DS_STORE)}')
        if clean_failed := self.ds_store.clean_failed:
            print(f'    {R_BOLD}Failed to clean{C.END} {self._entry_analysis("bold", 0, clean_failed, insert=DS_STORE, percent=False)}')
        if scanned := self.ds_store.scanned:
            print(f'    {P_BOLD}Found{C.END} {self._entry_analysis("bold", 0, scanned, insert=DS_STORE)}')

        if self.dot_underscored.total_entries + self.dot_any_size.total_entries + self.dot_not_matching.total_entries + self.dot_underscored_only.total_entries:
            dot_total_removed = self.dot_underscored.cleaned + self.dot_any_size.cleaned + self.dot_not_matching.cleaned + self.dot_underscored_only.cleaned
            dot_total_remove_failed = self.dot_underscored.clean_failed + self.dot_any_size.clean_failed + self.dot_not_matching.clean_failed + self.dot_underscored_only.clean_failed
            # dot_total_scanned = self.dot_underscored.scanned + self.dot_any_size.scanned + self.dot_not_matching.scanned + self.dot_underscored_only.scanned

            if dot_total_removed:
                print(f'    {B_BOLD}Cleaned{C.END} {self._entry_analysis("bold", 0, dot_total_removed, insert=DOT_UNDERSCORED)}')
            elif not dot_total_remove_failed:
                print(f'    {P_BOLD}Found{C.END} {self._entry_analysis("bold", 0, self.dot_underscored.scanned, insert=DOT_UNDERSCORED)}')
            if dot_total_remove_failed:
                print(f'    {R_BOLD}Failed to clean{C.END} {self._entry_analysis("bold", 0, dot_total_remove_failed, insert=DOT_UNDERSCORED)}')

            if self.dot_any_size.total_entries + self.dot_not_matching.total_entries + self.dot_underscored_only.total_entries:
                print(f"    {C.ITALIC}in detail:{C.END}")

                if cleaned := self.dot_underscored.cleaned:
                    print(f'        {B_BOLD}Cleaned{C.END} {self._entry_analysis("bold", 0, cleaned, insert=DOT_UNDERSCORED)}')
                if clean_failed := self.dot_underscored.clean_failed:
                    print(f'        {R_BOLD}Failed to clean{C.END} {self._entry_analysis("bold", 0, clean_failed, insert=DOT_UNDERSCORED)}')
                if found := self.dot_underscored.scanned:
                    print(f'        {P_BOLD}Found{C.END} {self._entry_analysis("bold", 0, found, insert=DOT_UNDERSCORED)}')

                if cleaned := self.dot_any_size.cleaned:
                    print(f'        {B_BOLD}Cleaned{C.END} {self._entry_analysis("bold", 0, cleaned, insert=f"{C.RED}{C.ITALIC}not conventionally sized{C.END} {DOT_UNDERSCORED}")}')
                if clean_failed := self.dot_any_size.clean_failed:
                    print(f'        {R_BOLD}Failed to clean{C.END} {self._entry_analysis("bold", 0, clean_failed, insert=f"{C.RED}{C.ITALIC}not conventionally sized{C.END} {DOT_UNDERSCORED}")}')
                if found := self.dot_any_size.scanned:
                    print(f'        {C.FAINT}Found{C.END} {self._entry_analysis("faint", 0, found, insert=f"{C.RED}{C.ITALIC}{C.UNDERLINE}{C.FAINT}not conventionally sized{C.END} {C.FAINT}._*{C.END}", faint=True)}')

                if cleaned := self.dot_not_matching.cleaned:
                    print(f'        {B_BOLD}Cleaned{C.END} {self._entry_analysis("bold", 0, cleaned, insert=f"{C.RED}{C.ITALIC}not matching{C.END} {DOT_UNDERSCORED}")}')
                if clean_failed := self.dot_not_matching.clean_failed:
                    print(f'        {R_BOLD}Failed to clean{C.END} {self._entry_analysis("bold", 0, clean_failed, insert=f"{C.RED}{C.ITALIC}not matching{C.END} {DOT_UNDERSCORED}")}')
                if found := self.dot_not_matching.scanned:
                    print(f'        {C.FAINT}Found{C.END} {self._entry_analysis("faint", 0, found, insert=f"{C.RED}{C.ITALIC}{C.UNDERLINE}{C.FAINT}not matching{C.END} {C.FAINT}._*{C.END}", faint=True)}')

                if cleaned := self.dot_underscored_only.cleaned:
                    print(f'        {B_BOLD}Cleaned{C.END} {self._entry_analysis("bold", 0, cleaned, insert=f"{C.RED}{C.ITALIC}not matching and not conventionally sized{C.END} {DOT_UNDERSCORED}")}')
                if clean_failed := self.dot_underscored_only.clean_failed:
                    print(f'        {R_BOLD}Failed to clean{C.END} {self._entry_analysis("bold", 0, clean_failed, insert=f"{C.RED}{C.ITALIC}not matching and not conventionally sized{C.END} {DOT_UNDERSCORED}")}')
                if found := self.dot_underscored_only.scanned:
                    print(f'        {C.FAINT}Found{C.END} {self._entry_analysis("faint", 0, found, insert=f"{C.RED}{C.ITALIC}{C.UNDERLINE}{C.FAINT}not matching and not conventionally sized{C.END} {C.FAINT}._*{C.END}", faint=True)}')

        # if analysis_exists and not self.is_cleaning and not self.enumerate_scanned:
        #     print(f"{C.ITALIC}Note{C.END}: add --enumerate flag to examine.")

    def dictionary_report(self) -> dict:
        return dict(
            scanned_files=self.scanned_files,
            scanned_dirs=self.scanned_dirs,
            scan_failed_dirs=self.scan_failed_dirs,
            bad_unicode_base_path=self.bad_unicode_base_path,
            ds_store=self.ds_store.as_dict(),
            bad_unicode_dir=self.bad_unicode_dir.as_dict(),
            bad_unicode_file=self.bad_unicode_file.as_dict(),
            dot_underscored=self.dot_underscored.as_dict(),
            dot_any_size=self.dot_any_size.as_dict(),
            dot_not_matching=self.dot_not_matching.as_dict(),
            dot_underscored_only=self.dot_underscored_only.as_dict(),
        )

    def _initialize_counters(self) -> None:
        self.scanned_files: int = 0
        self.scanned_dirs: int = 0
        self.scan_failed_dirs: int = 0
        self.bad_unicode_base_path: bool = False
        self.ds_store: CleanStatus = CleanStatus(fix=self.remove_ds_store)
        self.bad_unicode_dir: CleanStatus = CleanStatus(fix=self.replace_bad_unicode)
        self.bad_unicode_file: CleanStatus = CleanStatus(fix=self.replace_bad_unicode)
        self.dot_underscored: CleanStatus = CleanStatus(fix=self.remove_dot_underscored)
        self.dot_any_size: CleanStatus = CleanStatus(fix=self.remove_dot_any_size)
        self.dot_not_matching: CleanStatus = CleanStatus(fix=self.remove_dot_not_matching)
        self.dot_underscored_only: CleanStatus = CleanStatus(fix=self.remove_dot_any_size or self.remove_dot_not_matching)

    @staticmethod
    def _unlink(file: Path) -> None:
        os.unlink(normalize("NFC", str(file)))

    @staticmethod
    def _path_repr(path: Path | str) -> str:
        return f"{C.UNDERLINE}{C.BOLD}{path}{C.END}"

    def _on_walk_error(self, error: OSError) -> None:
        path = Path(error.filename)
        if self.enumerate_error:
            if error_repr := str(error):
                print(f"{C.RED}{C.ITALIC}failed to access directory {C.END}{C.RED}({C.BOLD}{type(error).__name__}{C.END}{C.RED}: {error_repr}):{C.END} {self._path_repr(path)}")
            else:
                print(f"{C.RED}{C.ITALIC}failed to access directory {C.END}{C.RED}({C.BOLD}{type(error).__name__}{C.END}{C.RED}):{C.END} {self._path_repr(path)}")
        self.scan_failed_dirs += 1
        self.scanned_dirs -= 1

    def _print_error(self, message: str, path: Path, error: BaseException) -> None:
        if self.enumerate_error:
            if error_repr := str(error):
                print(f"{C.RED}{C.ITALIC}{message} {C.END}{C.RED}({C.BOLD}{type(error).__name__}{C.END}{C.RED}: {error_repr}{C.RED}):{C.END} {self._path_repr(path)}")
            else:
                print(f"{C.RED}{C.ITALIC}{message} {C.END}{C.RED}({C.BOLD}{type(error).__name__}{C.END}{C.RED}):{C.END} {self._path_repr(path)}")

    def _enumerate(self, message: str, path: Path | str, condition: bool) -> None:
        if condition:
            print(f"{message}:{C.END} {self._path_repr(path)}")

    @staticmethod
    def _wrap(
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

    def _entry_analysis(
        self,
        color,
        directories: int,
        files: int,
        *,
        insert: str = "",
        add_space: bool = True,
        percent: bool = True,
        insert_before_percent: str = "",
        faint: bool = False,
    ) -> str:
        if insert and add_space:
            insert += " "
        if insert_before_percent and add_space:
            insert_before_percent = " " + insert_before_percent

        if faint:
            if directories:
                raise ValueError("directories with faint is not currently implemented")
            if not percent:
                raise ValueError("this should include percent")
            if color != "faint":
                raise ValueError("color should be faint")
            return f'{self._wrap(color, files, f"{insert}{C.FAINT}file", f"{insert}{C.FAINT}files")}{insert_before_percent} {C.FAINT}({self._wrap("bold", files / (self.scanned_files or 1), percent=True)}{C.FAINT}, among files){C.END}'

        match directories, files:
            # case 0, 0:
            #     raise ValueError("this should not be evoked")
            case 0, files:
                if percent:
                    return f'{self._wrap(color, files, f"{insert}file", f"{insert}files")}{insert_before_percent} ({self._wrap("bold", files / (self.scanned_files or 1), percent=True)}, among files)'
                else:
                    return f'{self._wrap(color, files, f"{insert}file", f"{insert}files")}{insert_before_percent}'
            case directories, 0:
                if percent:
                    return f'{self._wrap(color, directories, f"{insert}directory", f"{insert}directories")}{insert_before_percent} ({self._wrap("bold", directories / (self.scanned_dirs or 1), percent=True)}, among directories)'
                else:
                    return f'{self._wrap(color, directories, f"{insert}directory", f"{insert}directories")}{insert_before_percent}'
            case directories, files:
                if percent:
                    return f'{self._wrap(color, directories, f"{insert}directory", f"{insert}directories")} and {self._wrap(color, files, f"{insert}file", f"{insert}files")}{insert_before_percent} ({self._wrap("bold", (files + directories) / (self.scanned_dirs + self.scanned_files or 1), percent=True)}, {self._wrap(color, directories + files)} in total)'
                else:
                    return f'{self._wrap(color, directories, f"{insert}directory", f"{insert}directories")} and {self._wrap(color, files, f"{insert}file", f"{insert}files")}{insert_before_percent} ({self._wrap(color, directories + files)} in total)'
