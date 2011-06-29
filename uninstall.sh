#!/bin/sh 

buildDir="./build"

if [ ! -d ${buildDir} ]
then mkdir build || exit
fi


cd ${buildDir} || exit
make uninstall || exit

../script/timekpr.postrm $1