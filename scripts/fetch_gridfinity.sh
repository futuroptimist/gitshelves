#!/usr/bin/env sh
set -eu
revision=910e22d8607fd7f5f51ad5e5cbc5287a76810bfd
url=https://github.com/kennetek/gridfinity-rebuilt-openscad.git
rm -rf openscad/lib/gridfinity-rebuilt
git clone "$url" openscad/lib/gridfinity-rebuilt
git -C openscad/lib/gridfinity-rebuilt checkout --detach "$revision"
test -f openscad/lib/gridfinity-rebuilt/LICENSE
