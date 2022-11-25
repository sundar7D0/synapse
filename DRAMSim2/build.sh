#Cleaning existing junk
#make clean
#rm DRAMSim.py* _DRAMSim.so DRAMSim_wrap.c DRAMSim_wrap.o
#rm Callback.py _Callback.so Callback_wrap.c Callback_wrap.o
#Compiling DRAMSim
#make

#Compiling 
#swig -c++ -python DRAMSim.i
#g++ -fpic -O3 -c DRAMSim_wrap.cxx -o DRAMSim_wrap.o -I/usr/include/python3.5m
#g++ -shared *.o -o _DRAMSim.so

swig -python -c++ DRAM.i
g++ -fPIC -O3 -c Memifc.cpp DRAM_wrap.cxx -I/usr/include/python3.5m
g++ -shared *.o -o _DRAM.so
cp DRAM.py _DRAM.so ..

#swig -c++ -python Callback.i
#g++ -fpic -O3 -c Callback_wrap.cxx -o Callback_wrap.o -I/usr/include/python3.5m
#g++ -shared *.o -o _Callback.so
