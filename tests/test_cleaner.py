import os.path
from pathlib import Path
import shutil
from unicodedata import normalize

from mrg._cleaner import Cleaner

TEST_DIR = Path(__file__).parent / "files"

def setup_test():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    TEST_DIR.mkdir(parents=True)
    TEST_DIR.joinpath(".DS_Store").touch()
    TEST_DIR.joinpath("._.DS_Store").touch()
    TEST_DIR.joinpath(normalize("NFD", "나쁜 파일")).touch()
    TEST_DIR.joinpath(normalize("NFC", "좋은 파일")).touch()
    TEST_DIR.joinpath(normalize("NFD", "나쁜 폴더")).mkdir()
    TEST_DIR.joinpath(normalize("NFC", "좋은 폴더")).mkdir()
    normal_folder = TEST_DIR.joinpath("normal folder")
    normal_folder.mkdir()
    normal_folder.joinpath("normal file").touch()
    normal_folder.joinpath("normal file2").touch()
    normal_folder.joinpath("._normal file").write_bytes(b"4" * 4096)
    normal_folder.joinpath("._no_matching_file").write_bytes(b"4" * 4096)
    normal_folder.joinpath("._no_matching_and_any_size").write_bytes(b"123")

def test_cleaner():
    setup_test()
    cleaner = Cleaner(
        TEST_DIR,
        enumerate_cleaned=False,
        remove_ds_store=True,
        replace_bad_unicode=True,
        remove_dot_underscored=True,
        remove_dot_any_size=True,
        remove_dot_not_matching=True,
        follow_symlinks=False,
    )
    cleaner.clean()
    assert cleaner.dictionary_report() == {
        'scanned_files': 9,
        'ds_store': 1,
        'bad_unicode_base_path': False,
        'bad_unicode_dir': 1,
        'bad_unicode_file': 1,
        'dot_underscored': 1,
        'dot_any_size': 1,
        'dot_not_matching': 1,
        'dot_underscored_only': 1,
        'ds_store_fixed': True,
        'bad_unicode_fixed': True,
        'dot_underscored_fixed': True,
        'dot_any_size_fixed': True,
        'dot_not_matching_fixed': True
    }

    walk_iter = iter(os.walk(TEST_DIR))
    root, dirs, files = next(walk_iter)
    assert set(dirs) == {'좋은 폴더', '나쁜 폴더', 'normal folder'}
    assert set(files) == {'나쁜 파일', '좋은 파일'}
    dirs[:] = ['좋은 폴더', '나쁜 폴더', 'normal folder']
    assert next(walk_iter) == (os.path.join(root, "좋은 폴더"), [], [])
    assert next(walk_iter) == (os.path.join(root, "나쁜 폴더"), [], [])
    normal_folder, dirs, files = next(walk_iter)
    assert normal_folder == os.path.join(root, 'normal folder')
    assert dirs == []
    assert set(files) == {'normal file2', 'normal file'}
