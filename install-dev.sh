#!/bin/sh

buildDir="./build"

if [ ! -d ${buildDir} ]; then
  mkdir build || exit
fi

cd ${buildDir} || exit
cmake -DCMAKE_INSTALL_PREFIX=`kde4-config --prefix` ../src || exit
make || exit
sudo make install || exit

sudo cp ../testfile/timekpr.conf /etc/timekpr/timekpr.conf
