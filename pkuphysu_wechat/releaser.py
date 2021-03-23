import os
import sys
import zipfile
from distutils.sysconfig import get_python_lib

import click
from pip._internal.req.constructors import install_req_from_line
from pip._internal.req.req_uninstall import UninstallPathSet
from pip._internal.utils.misc import get_distribution

PROJECT_FILE_EXCLUDE = ["releaser.py", ".secrets.local.toml"]
PACKAGE_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(PACKAGE_ROOT)


def dumb_print(filename):
    term_size = os.get_terminal_size().columns
    filename = filename[:term_size]
    filename += " " * (term_size - len(filename))
    sys.stdout.write("\r" + filename)
    sys.stdout.flush()


def zip_info_fixer(name):
    info = zipfile.ZipInfo(name)
    info.external_attr = 0o666 << 16
    return info


def zip_code(zf):
    zf.writestr(
        zip_info_fixer("index.py"),
        "from pkuphysu_wechat.wsgi_wrapper import main",
    )

    for dirname, _, files in os.walk(PACKAGE_ROOT):
        for filename in files:
            if filename in PROJECT_FILE_EXCLUDE:
                continue
            path = os.path.join(dirname, filename)
            path_in_zip = os.path.relpath(path, PROJECT_ROOT)
            dumb_print(path_in_zip)
            zf.write(path, path_in_zip)


def zip_lib(zf):
    assert sys.version_info[:2] == (3, 6) and sys.platform == "linux"
    lib_path = get_python_lib()
    poetry_pf = os.popen("poetry export --without-hashes")
    for req_line in poetry_pf.readlines():
        if "==" not in req_line:
            continue
        req = install_req_from_line(req_line)
        dist = get_distribution(req.name)
        for path in UninstallPathSet.from_dist(dist).paths:
            path_in_zip = os.path.relpath(path, lib_path)
            if not path_in_zip.startswith(".."):
                dumb_print(path_in_zip)
                zf.write(path, path_in_zip)


@click.command()
@click.option("--code", "-c", is_flag=True, help="Bundle code.")
@click.option("--dep", "-d", is_flag=True, help="Bundle dependencies.")
def main(code: bool, dep: bool):
    if not code and not dep:
        raise click.UsageError("Must bundle something.")

    zipname = "release"
    if code:
        zipname += "-code"
    if dep:
        zipname += "-dep"

    with zipfile.ZipFile(f"{zipname}.zip", "w") as zf:
        if code:
            zip_code(zf)
        if dep:
            zip_lib(zf)
