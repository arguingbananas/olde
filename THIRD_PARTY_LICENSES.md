# Third-party licenses

Olde is MIT-licensed and is distributed as source only. It vendors, copies and
modifies no outside code, and the packages below are installed separately by
`pip`, so their license texts come with them rather than with Olde.

Each license was read from the license file of the version pinned or installed
at the time of writing (for GitHub Actions, the pinned commit). Versions change
as dependencies are updated; the licenses rarely do.

## Runtime packages (`requirements.txt` and what it pulls in)

| Package | Version | License |
|---|---|---|
| [anthropic](https://github.com/anthropics/anthropic-sdk-python) | 2.8.0 | Apache-2.0 |
| [feedparser](https://github.com/kurtmckee/feedparser) | 6.0.14 | BSD-2-Clause |
| [Flask](https://github.com/pallets/flask) | 3.1.3 | BSD-3-Clause |
| [pydantic](https://github.com/pydantic/pydantic) | 2.14.3 | MIT |
| [requests](https://github.com/psf/requests) | 2.34.2 | Apache-2.0 |
| [annotated-types](https://github.com/annotated-types/annotated-types) | 0.8.0 | MIT |
| [anyio](https://github.com/agronholm/anyio) | 4.16.0 | MIT |
| [blinker](https://github.com/pallets-eco/blinker) | 1.9.0 | MIT |
| [certifi](https://github.com/certifi/python-certifi) | 2026.10.23 | MPL-2.0 (used unmodified) |
| [charset-normalizer](https://github.com/jawah/charset_normalizer) | 3.5.2 | MIT |
| [click](https://github.com/pallets/click) | 8.5.1 | BSD-3-Clause |
| [docstring_parser](https://github.com/rr-/docstring_parser) | 0.18.0 | MIT |
| [feedparser-sgmllib](https://github.com/python-syndication/feedparser-sgmllib) | 2.1.0 | PSF-2.0 |
| [h11](https://github.com/python-hyper/h11) | 0.16.0 | MIT |
| [httpcore2](https://github.com/pydantic/httpx2) | 2.16.0 | BSD-3-Clause |
| [httpx2](https://github.com/pydantic/httpx2) | 2.16.0 | BSD-3-Clause |
| [idna](https://github.com/kjd/idna) | 3.20 | BSD-3-Clause |
| [itsdangerous](https://github.com/pallets/itsdangerous) | 2.2.0 | BSD-3-Clause |
| [Jinja2](https://github.com/pallets/jinja) | 3.1.6 | BSD-3-Clause |
| [jiter](https://github.com/pydantic/jiter) | 0.19.0 | MIT |
| [MarkupSafe](https://github.com/pallets/markupsafe) | 3.0.4 | BSD-3-Clause |
| [opentelemetry-api](https://github.com/open-telemetry/opentelemetry-python) | 1.45.2 | Apache-2.0 |
| [pydantic_core](https://github.com/pydantic/pydantic) | 2.50.4 | MIT |
| [sniffio](https://github.com/python-trio/sniffio) | 1.3.1 | MIT or Apache-2.0 |
| [truststore](https://github.com/sethmlarson/truststore) | 0.10.5 | MIT |
| [typing_extensions](https://github.com/python/typing_extensions) | 4.16.0 | PSF-2.0 |
| [typing-inspection](https://github.com/pydantic/typing-inspection) | 0.4.5 | MIT |
| [urllib3](https://github.com/urllib3/urllib3) | 2.8.0 | MIT |
| [Werkzeug](https://github.com/pallets/werkzeug) | 3.1.9 | BSD-3-Clause |

## Development tools (`requirements-dev.txt` and what it pulls in)

| Package | Version | License |
|---|---|---|
| [pytest](https://github.com/pytest-dev/pytest) | 9.2.0 | MIT |
| [ruff](https://github.com/astral-sh/ruff) | 0.17.5 | MIT |
| [pip-audit](https://github.com/pypa/pip-audit) | 2.10.1 | Apache-2.0 |
| [zizmor](https://github.com/zizmorcore/zizmor) | 1.33.1 | MIT |
| [actionlint-py](https://github.com/Mateusz-Grzelinski/actionlint-py) | 1.7.12.25 | MIT |
| [boolean.py](https://github.com/bastikr/boolean.py) | 5.0 | BSD-2-Clause |
| [CacheControl](https://github.com/psf/cachecontrol) | 0.14.4 | Apache-2.0 |
| [cyclonedx-python-lib](https://github.com/CycloneDX/cyclonedx-python-lib) | 11.12.0 | Apache-2.0 |
| [defusedxml](https://github.com/tiran/defusedxml) | 0.7.1 | PSF-2.0 |
| [filelock](https://github.com/tox-dev/filelock) | 4.2.10 | MIT |
| [iniconfig](https://github.com/pytest-dev/iniconfig) | 2.3.1 | MIT |
| [license-expression](https://github.com/aboutcode-org/license-expression) | 30.4.4 | Apache-2.0 |
| [markdown-it-py](https://github.com/executablebooks/markdown-it-py) | 4.3.0 | MIT |
| [mdurl](https://github.com/executablebooks/mdurl) | 0.1.2 | MIT |
| [msgpack](https://github.com/msgpack/msgpack-python) | 1.2.4 | Apache-2.0 |
| [packageurl-python](https://github.com/package-url/packageurl-python) | 0.17.6 | MIT |
| [packaging](https://github.com/pypa/packaging) | 26.3 | Apache-2.0 or BSD-2-Clause |
| [pip-api](https://github.com/di/pip-api) | 0.0.35 | Apache-2.0 |
| [pip-requirements-parser](https://github.com/nexB/pip-requirements-parser) | 32.0.1 | MIT |
| [platformdirs](https://github.com/tox-dev/platformdirs) | 4.14.5 | MIT |
| [pluggy](https://github.com/pytest-dev/pluggy) | 1.7.0 | MIT |
| [py-serializable](https://github.com/madpah/serializable) | 2.2.0 | Apache-2.0 |
| [Pygments](https://github.com/pygments/pygments) | 2.21.0 | BSD-2-Clause |
| [pyparsing](https://github.com/pyparsing/pyparsing) | 3.3.3 | MIT |
| [rich](https://github.com/Textualize/rich) | 15.0.0 | MIT |
| [sortedcontainers](https://github.com/grantjenks/python-sortedcontainers) | 2.4.0 | Apache-2.0 |
| [tomli](https://github.com/hukkin/tomli) | 2.5.0 | MIT |
| [tomli_w](https://github.com/hukkin/tomli-w) | 1.2.0 | MIT |

## Other software

| Software | Used for | License |
|---|---|---|
| [Python](https://www.python.org) | Runs Olde | PSF-2.0 |
| [Ollama](https://github.com/ollama/ollama) | Optional local translation | MIT |
| [Qwen 3.5](https://ollama.com/library/qwen3.5) (`qwen3.5:4b`) | Optional local model | Apache-2.0 |
| [actionlint](https://github.com/rhysd/actionlint) 1.7.12 | Workflow checks (downloaded by actionlint-py) | MIT |
| [actions/checkout](https://github.com/actions/checkout) | CI | MIT |
| [actions/setup-python](https://github.com/actions/setup-python) | CI | MIT |
| [dependabot/fetch-metadata](https://github.com/dependabot/fetch-metadata) | Dependabot auto-merge | MIT |

Olde ships no fonts or images; the page uses fonts already on your computer.
