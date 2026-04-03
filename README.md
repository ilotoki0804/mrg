# mrg - A tool for removing miscellaneous files created on macOS

[![Sponsoring](https://img.shields.io/badge/Sponsoring-Patreon-blue?logo=patreon&logoColor=white)](https://www.patreon.com/ilotoki0804)
[![Download Status](https://img.shields.io/pypi/dm/mrg)](https://pypi.org/project/mrg/)
[![License](https://img.shields.io/pypi/l/mrg.svg)](https://github.com/ilotoki0804/mrg/blob/main/LICENSE)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/mrg.svg)](https://pypi.org/project/mrg/)
[![Latest Version](https://img.shields.io/pypi/v/mrg)](https://pypi.org/project/mrg/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/ilotoki0804/mrg/blob/main/pyproject.toml)
<!-- ![Hits](https://hitscounter.dev/api/hit?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2mrg&label=Hits&icon=github&color=%234dc81f) -->

mrg is a CLI utility used to clean miscellaneous files created on macOS, or to normalize file names with Unicode.

## Functions of mrg

* **NFC normalization of Unicode file names** (`--bad-unicode`): Normalizes Unicode included in file or directory names to NFC.
* **Delete `.DS_Store` files** (`--ds-store`): Deletes `.DS_Store` files that are created when a folder is viewed in Finder.
* **Delete `._*` files** (`--dot`): Deletes `._*` files that store metadata or indexing information on macOS.

## Features of mrg

* **ANSI color support**: mrg supports nice terminal colors. Through colors, you can check the state of directories intuitively. you can also disable it through the [`NO_COLOR`](https://no-color.org/) environment variable.
* **Pretty analysis reports**: When you scan or clean through mrg, it provides a pretty analysis of the result. Through this, you can check at a glance what mrg scanned and cleaned.
* **JSON analysis reports**: In addition to pretty analysis for humans, it also provides analysis in JSON format that machines can read.
* **Python API support**: mrg can also be used as a Python module. Through the Python `mrg` module, you can run mrg through Python or customize it.
* **No external dependencies**: At runtime, mrg does not use any external libraries besides libraries provided by Python by default. If you want tests, you need to install the development dependency pytest, but it is not installed at runtime.

## Installation

You can install mrg through homebrew.

```bash
brew tap ilotoki0804/homebrew-mrg
brew install mrg
```


You can also use mrg directly through [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
After installing uv, enter the command below.

```bash
uvx mrg --help
```

If you installed through `uv`, use `uvx mrg` instead of `mrg`.

```bash
uvx mrg . --enumerate ...
```

mrg is a package [registered on PyPI](https://pypi.org/project/mrg/), so you can also download and use it from PyPI.

## Usage

mrg basically takes a path as an argument. To inspect a directory, enter a path after the `mrg` command as below.

```bash
mrg .
```

If written only like this without other arguments, it becomes "scan mode" by default.
In this state, it does not change any directory, and only inspects the state of the directory and then provides analysis results.

For example, an analysis result like this can be provided.

```
mrg have scanned 6515 directories and 482446 files (488961 in total) without making any changes
Analysis:
    Found 6285 not NFC normalized directories (96.47%, among directories)
    Found 1 ._* file (0.00%, among files)
```

Here it is not colorized separately, but if color is enabled, it is colorized so you can intuitively check important numbers at a glance.

As mentioned above, if you do not attach other arguments, it only analyzes directories and changes nothing.

To actually clean or modify files, you need to attach arguments. You can clean a directory by attaching one or more of the following arguments.

* `--dot`: Deletes `._*` files. By default, it deletes only when they have a normal size and a matching file exists.
* `--bad-unicode`: Normalizes Unicode file/folder names that are not NFC-normalized.
* `--ds-store`: Deletes `.DS_Store` files.

For example, to normalize all files and directories in the `.` directory to NFC, you can use the following command.

```bash
mrg . --bad-unicode
```

Below is an example of a possible result when this command is applied.

```
mrg have scanned 6515 directories and 482446 files (488961 in total) and cleaned/normalized 6285 directories and 3609 files (2.02%, 9894 in total)
Analysis:
    Normalized 6285 directories and 3609 files to NFC (2.02%, 9894 in total)
```

You can confirm that 6285 folders and 3609 files got normalized.

`--ds-store` and `--dot` are similar too. If you add the flags and run it, `.DS_Store` and `._*` files in folders are deleted respectively.

If you want to run `--bad-unicode`, `--ds-store`, and `--dot` all at once, you can use the `--all` flag.

```bash
mrg . --all
```

This lets you completely clean a directory simply.

### Explanation of each function

**`--bad-unicode`** normalizes cases where Unicode included in file or directory names is not NFC-normalized.
Windows supports only NFC-normalized Unicode, and macOS supports both NFC-normalized Unicode and NFD-normalized Unicode. If you normalize files and folders through mrg, you can obtain compatibility with external systems while still using files on macOS without problems.

**`--ds-store`** deletes discovered `.DS_Store` files, and this file is created when that folder is viewed in Finder. Therefore, for folders frequently viewed in Finder, it is wiser to leave this file than to keep deleting it, and it is good to use it when cleaning external storage where Finder is not frequently used.

**`--dot`** deletes `._*` files. Since this file contains information used for indexing, if you use indexing on macOS, the file will keep being created again.
If indexing is used, it will keep being created again, so it is recommended to use this when it does not need indexing and when there is a possibility of moving it to another device, or when cleaning external storage before moving it.

### Advanced commands

You can change mrg's behavior through several special commands.

* `--enumerate`: Enumerates all cleaned or modified files. If it is scan mode (when no cleanup argument is added), it enumerates all detected cleanable files.
* `--no-enumerate-error`: When scanning or cleaning fails, by default it outputs errors even if `--enumerate` is not set. If you turn on this flag, you can suppress error output even when failures occur.
* `--json`: After cleanup or scanning ends, it outputs a machine-readable cleanup report in JSON format instead of pretty analysis for humans. To feed values to a machine, turn on `--no-enumerate-error`.
* `--follow-symlinks`: Follows symbolic links while traversing directories.

### Advanced `--dot` command

`._*` files have two characteristics.

* A corresponding native file must exist in the same directory. For example, `._my file` always corresponds to `my file`, and this file exists in the same directory as `._my_file`.
* `._*` files always occupy 4kb (4096 bytes) or 176 bytes. This is based on my experience, and if this assumption is wrong, please let me know through an issue or similar.

Therefore, by default, the `--dot` command recognizes a file as `._*` only when both conditions are satisfied.

Still, you may want to delete files starting with `._` that do not satisfy one or both of these two conditions.
In that case, by adding the following commands, you can force those files to be deleted as well.

* `--dot-any-size`: If you add this flag, `._*` files are deleted regardless of their size.
* `--dot-not-matching`: If you add this flag, `._*` files are deleted even if the corresponding file does not exist.

If one or both of these two flags are used, `--dot` is implied. Therefore, you do not have to write the `--dot` flag explicitly.

However, if you use these two commands, files that are not actually `._*` files may also be deleted, so please take extra care.

If you want to use these two flags at the same time, you can use `--dot-all`. This is the same as `--dot --dot-any-size --dot-not-matching`.

## References

macOS provides a cli tool called `dot_clean` by default. Through this tool, `._*` files can also be cleaned, but `.DS_Store` cleanup or NFC normalization is not provided, and there is no way to use it outside macOS. In addition to `._*` files, mrg supports more diverse cleanup tools and can be used cross-platform.

* <https://en.wikipedia.org/wiki/.DS_Store>
* <https://wiki.mozilla.org/DS_Store_File_Format>
* <https://en.wikipedia.org/wiki/AppleSingle_and_AppleDouble_formats>
* <https://tldr.inbrowser.app/pages.ko/osx/dot_clean>
* <https://www.zeroonetwenty.com/blueharvest/>
