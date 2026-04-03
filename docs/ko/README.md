# mrg - macOS에서 생성되는 잡다한 파일들을 제거하는 툴

[![Sponsoring](https://img.shields.io/badge/Sponsoring-Patreon-blue?logo=patreon&logoColor=white)](https://www.patreon.com/ilotoki0804)
[![Download Status](https://img.shields.io/pypi/dm/mrg)](https://pypi.org/project/mrg/)
[![License](https://img.shields.io/pypi/l/mrg.svg)](https://github.com/ilotoki0804/mrg/blob/main/LICENSE)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/mrg.svg)](https://pypi.org/project/mrg/)
[![Latest Version](https://img.shields.io/pypi/v/mrg)](https://pypi.org/project/mrg/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/ilotoki0804/mrg/blob/main/pyproject.toml)
![Hits](https://hitscounter.dev/api/hit?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2mrg&label=Hits&icon=github&color=%234dc81f)

mrg는 macOS에서 생성되는 잡다한 파일들을 제거하거나 파일명을 유니코드로 정규화할 때 사용하는 CLI 유틸리티입니다.

mrg는 macOS에서 생성된 정크 파일들을 정리한다는 의미로, macOS와 쓰레기를 합성한 '멕레기'의 두문자어입니다.

## mrg의 기능

* **유니코드 파일명 NFC 정규화**(`--bad-unicode`): 파일 또는 디렉토리의 이름에 포함된 유니코드를 NFC로 정규화시킵니다.
* **`.DS_Store` 파일 삭제**(`--ds-store`): 폴더를 파인더로 열람했을 때 생성되는 `.DS_Store` 파일을 삭제합니다.
* **`._*` 파일 삭제**(`--dot`): macOS에서 메타데이터나 인덱싱 정보 등을 저장하는 `._*` 파일을 삭제시킵니다.

## mrg의 특징

* **ANSI 컬러 지원**: mrg는 예쁜 터미널 색상을 지원합니다. 색상을 통해 직관적으로 디렉토리의 상태를 확인하실 수 있습니다. 물론 [`NO_COLOR`](https://no-color.org/) 환경 변수를 통해서 비활성화도 가능합니다.
* **예쁜 분석 리포트 제공**: mrg를 통해 스캔하거나 정리할 경우 결과에 대해 예쁜 분석을 제공합니다. 이를 통해 mrg가 스캔하고 정리한 것들에 대해 한눈에 확인하실 수 있습니다.
* **json 분석 리포트 제공**: 인간을 위한 예쁜 분석에 더해 기계로 읽을 수 있는 JSON 형식의 분석 또한 제공됩니다.
* **python API 제공**: mrg는 파이썬 모듈로도 사용할 수 있습니다. 파이썬의 `mrg` 모듈을 통해 mrg를 파이썬을 통해 실행하거나 커스터마이즈할 수 있습니다.
* **외부 의존성 없음**: mrg는 런타임에서 파이썬에서 기본으로 제공하는 라이브러리 외에 어떠한 외부 라이브러리도 사용하지 않았습니다. 테스트를 원하면 개발 의존성인 pytest를 설치해야 하나 런타임에는 설치되지 않습니다.

## 설치하기

homebrew를 통해 mrg를 설치하실 수 있습니다.

```bash
brew tap ilotoki0804/homebrew-mrg
brew install mrg
```


[`uv`](https://docs.astral.sh/uv/getting-started/installation/)를 통해서도 mrg를 바로 사용하실 수 있습니다.
uv를 설치한 뒤 아래와 같은 명령어를 입력하세요.

```bash
uvx mrg --help
```

`uv`를 통해 설치하신 경우 `mrg` 대신 `uvx mrg`를 사용하시면 됩니다.

```bash
uvx mrg . --enumerate ...
```

mrg는 [PyPI에 등록](https://pypi.org/project/mrg/)된 패키지이므로 PyPI에서 다운로드해서도 사용하실 수 있습니다.

## 사용법

mrg는 기본적으로 path를 인자로 받습니다. 디렉토리를 검사하려면 아래와 같이 `mrg` 명령어 뒤에 경로를 입력하시면 됩니다.

```bash
mrg .
```

다른 인자 없이 이렇게만 작성할 경우 기본적으로 '스캔 모드'가 됩니다.
이 상태에서는 어떠한 디렉토리도 변경하지 않으며, 단순히 디렉토리의 상태를 조사한 뒤 분석 결과를 제공합니다.

예를 들어 다음과 같은 분석 결과가 제공될 수 있습니다.

```
mrg have scanned 6515 directories and 482446 files (488961 in total) without making any changes
Analysis:
    Found 6285 not NFC normalized directories (96.47%, among directories)
    Found 1 ._* file (0.00%, among files)
```

여기에서는 따로 컬러화가 되어 있지 않지만 컬러를 활성화했다면 컬러화가 되어 있어 직관적으로 중요한 숫자들을 한눈에 확인하실 수 있습니다.

상기한 대로 다른 인자를 붙이지 않을 경우 디렉토리를 분석하기만 하며 어떠한 것도 변경되지 않습니다.

실제로 파일을 정리하거나 수정하려면 인자를 붙여야 합니다. 다음의 인자 중 하나 이상을 붙여서 디렉토리를 정리할 수 있습니다.

* `--dot`: `._*` 파일을 삭제합니다. 기본적으로는 일반적인 크기를 가지고 있고 대응하는 파일이 존재하는 경우에만 삭제합니다.
* `--bad-unicode`: NFC 정규화되지 않은 유니코드 파일/폴더명을 정규화합니다.
* `--ds-store`: `.DS_Store` 파일을 삭제합니다.

예를 들어 `.` 디렉토리 내의 모든 파일과 디렉토리를 NFC로 정규화하려면 다음과 같은 코드를 사용할 수 있습니다.

```bash
mrg . --bad-unicode
```

아래는 해당 명령어를 적용시켰을 때의 나올 수 있는 결과의 예시입니다.

```
mrg have scanned 6515 directories and 482446 files (488961 in total) and cleaned/normalized 6285 directories and 3609 files (2.02%, 9894 in total)
Analysis:
    Normalized 6285 directories and 3609 files to NFC (2.02%, 9894 in total)
```

정규화가 안 되어 있던 6285개의 폴더와 3609개의 파일이 정규화되었음을 확인하실 수 있습니다.

`--ds-store`와 `--dot`도 비슷합니다. 플래그를 추가한 뒤 실행하면 각각 폴더 내의 `.DS_Store`와 `._*` 파일이 삭제됩니다.

만약에 `--bad-unicode`, `--ds-store`, `--dot`을 모두 동시에 실행하고 싶을 때는 `--all` 플래그를 사용하실 수 있습니다.

```bash
mrg . --all
```

이렇게 하면 간단하게 디렉토리를 완전히 정리하실 수 있습니다!

### 각 기능에 대한 설명

**`--bad-unicode`** 는 파일 또는 디렉토리의 이름에 포함된 유니코드가 NFC 정규화가 되어 있지 않은 경우 정규화시킵니다.
Windows는 NFC 정규화된 유니코드만을 지원하고, macOS는 NFC 정규화된 유니코드와 NFD 정규화된 유니코드 모두를 지원합니다. mrg를 통해 파일과 폴더를 정규화할 경우 외부 시스템과의 호환성을 얻으면서도 macOS에서도 파일을 문제 없이 사용하실 수 있습니다.

**`--ds-store`** 는 발견된 `.DS_Store` 파일을 삭제하는데, 이 파일은 해당 폴더를 파인더로 열람했을 때 생성됩니다. 따라서 파인더로 자주 열람하는 폴더의 경우 이 파일을 계속 지우기보단 남겨두는 것이 더 현명하고, 파인더를 자주 이용하지 않는 외장 스토리지를 정리할 때 사용하시면 좋습니다.

**`--dot`** 은 `._*` 파일을 삭제합니다. 이 파일은 인덱싱에 활용되는 정보이므로 macOS에서 인덱싱을 사용하시는 경우, 파일은 계속해서 다시 생성될 것입니다.
만약 인덱싱을 사용할 경우 계속해서 다시 생성될 것이므로, 인덱싱될 필요가 없고, 다른 장치로 이동할 가능성이 있거나 이동하기 전에 외장 스토리지를 정리할 때 사용하시는 것을 권장합니다.

### 고급 명령어

몇 가지 특수한 명령어를 통해 mrg의 행동을 변화시킬 수 있습니다.

* `--enumerate`: 모든 정리되거나 수정된 파일들을 열거합니다. 만약 스캔 모드(어떠한 정리 인자도 추가되지 않은 경우)일 경우 모든 감지된 정리할 수 있는 파일들을 열거합니다.
* `--no-enumerate-error`: 스캔이나 정리해 실패한 경우 기본적으로는 `--enumerate`를 설정하지 않아도 오류를 출력하도록 합니다. 이 플래그를 켜면 실패한 경우에도 오류를 출력하지 않도록 할 수 있습니다.
* `--json`: 정리나 스캔이 끝난 뒤 인간을 위한 예쁜 분석이 아니라 JSON 형식으로 된 기계가 이해할 수 있는 정리 리포트를 출력합니다. 기계에 값을 먹이려면 `--no-enumerate-error`를 켜세요.
* `--follow-symlinks`: 리텍토리를 순회하는 동안 심볼릭 링크를 따라갑니다.

### 고급 `--dot` 명령어

`._*` 파일은 두 가지 특성이 있습니다.

* 반드시 같은 디렉토리에 대응되는 원본 파일(native file)이 존재합니다. 예를 들어 `._my file`은 항상 `my file`에 대응되며, 이 파일은 `._my_file`과 같은 디렉토리에 존재합니다.
* `._*` 파일은 항상 4kb(4096바이트)나 176바이트를 차지합니다. 이는 제 경험에 의한 것으로, 만약 이 가정이 틀렸다면 이슈로 알려주십시오.

따라서 기본적으로 `--dot` 명령어는 두 조건을 모두 통과하는 경우에만 `._*` 파일로 인식합니다.

그렇지만 이 두 조건 중 하나 이상을 통과하지 못하는 `._`으로 시작하는 파일을 삭제하고 싶을 수 있습니다.
그런 경우에는 다음과 같은 명령어를 추가함으로써 그러한 파일들 또한 삭제하도록 강제할 수 있습니다.

* `--dot-any-size`: 이 플래그를 추가할 경우 `._*` 파일이 어떠한 크기를 가지건 삭제됩니다.
* `--dot-not-matching`: 이 플래그를 추가할 경우 `._*` 파일이 대응되는 파일이 존재하지 않더라도 삭제됩니다.

이 두 플래그 중 하나 이상을 사용할 경우 `--dot`이 암시됩니다. 따라서 `--dot` 플래그를 반드시 적을 필요는 없습니다.

다만 이 두 명령어를 사용하는 경우 실제로는 `._*`가 아닌 파일도 지워질 수 있으니 각별히 유의해 주세요.

이 두 플래그를 동시에 사용하고 싶은 경우 `--dot-all`을 사용하실 수 있습니다. 이는 `--dot --dot-any-size --dot-not-matching`과 동일합니다.

## 참고

macOS는 기본적으로 `dot_clean`이라는 cli 도구를 제공합니다. 이 툴을 통해서도 `._*` 파일들을 정리할 수 있으나 `.DS_Store` 정리나 NFC 정규화 기능은 제공되지 않으며 macOS 외부에서는 쓸 수 있는 방법이 없습니다. mrg는 `._*` 파일 외에도 더 다양한 정리 툴을 지원하며 크로스 플랫폼 사용이 가능합니다.

* <https://en.wikipedia.org/wiki/.DS_Store>
* <https://wiki.mozilla.org/DS_Store_File_Format>
* <https://en.wikipedia.org/wiki/AppleSingle_and_AppleDouble_formats>
* <https://tldr.inbrowser.app/pages.ko/osx/dot_clean>
* <https://www.zeroonetwenty.com/blueharvest/>
