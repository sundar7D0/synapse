#include "Memifc.h"
#include "DRAMSim.h"
#include <iostream>
#include <stdlib.h>
#include <queue>

void Memifc::read_complete(unsigned id, uint64_t address, uint64_t clock_cycle)
{
//  std::cout << "read complete - id: " << id << ", address: " << address << ", clock cycle: " << clock_cycle << std::endl;
  rv value;
  value.id = id;
  value.addr = address;
  value.clock_cycle = clock_cycle;
  read_responses.push(value);
}

void Memifc::write_complete(unsigned id, uint64_t address, uint64_t clock_cycle)
{
//  std::cout << "write complete - id: " << id << ", address: " << address << ", clock cycle: " << clock_cycle << std::endl;
  rv value;
  value.id = id;
  value.addr = address;
  value.clock_cycle = clock_cycle;
  write_responses.push(value);
}

uint64_t Memifc::get_current_time()
{
	return mem->getCurrentClockCycle();
}

void Memifc::update(uint64_t timestamp)
{
  while(true)
  {
    uint64_t t = mem->getCurrentClockCycle();
    
    if(t != timestamp)
      mem->update();
    else
      break;
  }
}

void power_callback(double a, double b, double c, double d)
{
  std::cout << "Power: " << a << " : " << b << " : " << c << " : " << d << std::endl;
}

Memifc::Memifc(std::string dram_config, std::string sys_config, std::string dir, std::string app_name, uint64_t size)
{
  mem = DRAMSim::getMemorySystemInstance(dram_config, sys_config, dir, app_name, size);
  read_cb = new DRAMSim::Callback<Memifc, void, unsigned, uint64_t, uint64_t>(this, &Memifc::read_complete);
  write_cb = new DRAMSim::Callback<Memifc, void, unsigned, uint64_t, uint64_t>(this, &Memifc::write_complete);
  mem->RegisterCallbacks(read_cb, write_cb, &power_callback);
}

void Memifc::request(uint64_t addr, bool is_write)
{
  mem->addTransaction(is_write, addr);
  //mem->addTransaction(is_write, (1LL << 33) | addr);
}

rv Memifc::read_response()
{
  while(read_responses.empty()){
    mem->update();
  }
  rv value = read_responses.front();
  read_responses.pop();
  return value;
}

rv Memifc::write_response()
{
  while(write_responses.empty())
    mem->update();

  rv value = write_responses.front();
  write_responses.pop();
  return value;
}

Memifc::~Memifc()
{
  free(mem);
}
