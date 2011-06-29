#!/bin/sh 

buildDir="./build"

if [ ! -d ${buildDir} ]
then mkdir build || exit
fi


cd ${buildDir} || exit
cmake -DCMAKE_INSTALL_PREFIX=`kde4-config --prefix` ../src || exit
make || exit
make install || exit
kbuildsycoca4 || exit

../script/timekpr.postinst