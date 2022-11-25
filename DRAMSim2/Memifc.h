#include <stdio.h>
#include "DRAMSim.h"
#include <queue>

typedef struct retval
{
  unsigned id;
  uint64_t addr;
  uint64_t clock_cycle;
}rv;

class Memifc
{
  private:
    void read_complete(unsigned, uint64_t, uint64_t);
    void write_complete(unsigned, uint64_t, uint64_t);
    //void power_callback(double a, double b, double c, double d);
    DRAMSim::MultiChannelMemorySystem *mem;
    DRAMSim::TransactionCompleteCB *read_cb, *write_cb;

    std::queue<rv> read_responses;
    std::queue<rv> write_responses;

  public:
   Memifc(std::string, std::string, std::string, std::string, uint64_t);
   void request(uint64_t, bool);
   void update(uint64_t);
   uint64_t get_current_time();
	 rv read_response();
   rv write_response();
   ~Memifc();
};
