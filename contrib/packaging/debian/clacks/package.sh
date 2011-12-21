#!/bin/sh
NAME=clacks
VERSION=`parsechangelog | sed -n 's/^Version:\s*//p'`

#----

if [ ! -x package.sh -o ! -d debian ]; then
	echo "This script needs to be run inside of its directory and as part of a git clone."
	exit 1
fi

echo -n "Processing... "

DIR="$NAME-$VERSION"
HERE=`pwd`
ROOT=`git rev-parse --show-toplevel`

# Create target directory
[ -d "$DIR" ] && rm -rf "$DIR"
mkdir "$DIR"

# Export the current git tree to the temporary directory
cd "$ROOT" && git archive master | tar -x -C "$HERE/$DIR"

# Create the orig.tar
cd "$HERE"
#TODO: remove me later on
rm -rf "$DIR/plugins"
tar cfj ${NAME}_${VERSION}.orig.tar.bz2 "$DIR"
cp -a debian "$DIR"
dpkg-source -b "$DIR" > /dev/null || exit 1

echo "done"
