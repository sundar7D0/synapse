# Synapse: Systolic CNN Accelerator’s Mapper-Simulator Environment
Systolic arrays are one of the most popular compute substrates within DL accelerators today, as they provide extremely high efficiency for running dense matrix multiplications by re-using operands through local data shifts. One such effort by [RISE lab](https://shakti.org.in/) at IIT Madras is [ShaktiMAAN](https://github.com/iitm-sysdl/SHAKTIMAAN), an open-source DNN accelerator for inference on edge devices based on systolic arrays.

![systolic block diagram](./images/systolic_block.png)

The complexity of this accelerator poses a variety of challenges in:
1. Hardware verification
2. Bottleneck analysis using performance modelling
3. Design space trade-offs
4. Efficient mapping strategy
5. Compiler optimizations

To tackle these challenges, I built Synapse (SYstolic CNN Accelerator’s MaPper-Simulator Environment): a versatile python based mapper-simulator environment. This work, done under the guidance of [Prof. Pratyush Kumar](http://www.cse.iitm.ac.in/~pratyush/) was submitted as my Bachelor's thesis at [IIT Madras](https://www.iitm.ac.in/).

![synapse overview](./images/synapse_overview.PNG)

## Key Contributions:
* Mapper that generates instruction trace given any workload, knob values for a targeted architecture.
* Functional simulator cost model for ShaktiMAAN.
* An RL agent that interacts with the mapper-simulator environment to search through the design space to find optimal hardware (array, buffer size), software (network folds, loop order) co-design knobs.

![synapse task flow](./images/synapse_task_flow.PNG)

## Dependencies
1. [Installing Bluespec](https://github.com/B-Lang-org/bsc)
2. [Installing verilator](https://www.veripool.org/verilator/)

## Using SHAKTIMAAN

### Software compilation
In the first step, instructions for SHAKTIMAAN are generated using a separate compilation process. More details to follow.  Instructions are compiled and stored in RAM, which is loaded when the testbench is initiated directly from `code.mem`. More to follow.

### Configuration
A testbench is available in `src/Soc.bsv` which instantiates the accelerator and runs a single trace of instructions.
All configurations can be changed adhering to the provisos required for compilation of Bluespec files and can be changed in `src/Soc.bsv`.
Non configurable parameters, such as ISA definitions, are defined in `src/commons/systolic.defines`.

### Verilog generation
1. `cd src`
2. `make generate_verilog` - generates Verilog files from Bluespec for all files.

### Simulation
1. `cd src`
2. `make generate_verilog`
3. `make link_verilator` - generates a binary `bin/out` which simulates the array.

## Additional resources
1. [Bachelor's thesis](https://drive.google.com/file/d/1PMTwZhSbaysdSdLks98JykyDDe_itRQa/view?usp=sharing)
2. [Presentation slides](https://drive.google.com/file/d/1NnDDXgM6h1zbRrv5gJUAIdI9pAYBtN9T/view?usp=sharing)
