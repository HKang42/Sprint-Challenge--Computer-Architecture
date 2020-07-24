"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):#, reg = [0] * 8, pc = 0, sp = None):
        """Construct a new CPU."""
        self.reg = [0] * 8      # General Purpose Registers
        self.ram = [0] * 256    # RAM
        self.sp = self.reg[7]  # Stack Pointer
        
        # Internal Registers
        self.pc = 0             # Program Counter
        self.ir = 0b00000001    # Instruction register (defaults to halt)
        self.fl = 0b00000000    # Flags (format is 00000LGE)


    def load(self):
        """Load a program into memory."""

        address = 0

        # Make sure a program file has been provided
        if len(sys.argv) != 2:
            print("Please provide a valid program file (e.g. cpu.py print8.ls8)")
            sys.exit(1)

        # Load file and write contents to memory (self.ram)
        program_file = 'examples/' + sys.argv[1] + '.ls8'
        try:
            with open(program_file) as f:
                for line in f:
                    try:
                        line = line.split("#", 1)[0]
                        line = int(line, 2)
                        self.ram_write(address, line)
                        address += 1
                    
                    # skip empty lines and lines without numbers
                    except ValueError:
                        pass
        
        # If file cannot be found
        except FileNotFoundError:
            print('File "{}" not found'.format(program_file))
            sys.exit(1)


    def alu(self, op, reg_a, reg_b):
        """
        ALU operations.
        Given an operation and the address/index number for 2 registers,
        perform the requested operation between the 2 values stored in the resgisters.

        Ex:
            Call: self.alu('ADD', 00000000, 00000001)
            Return: register[00000000] + register[00000001]
        """
        
        A = self.reg[reg_a]
        B = self.reg[reg_b]

        ### Arithmetic Operations
        if op == "ADD":
            return A + B
        
        elif op == "SUB":
            return A - B

        elif op == 'MUL':
            return A * B

        elif op == "DIV":
            return A / B

        elif op == 'MOD':
            if B == 0:
                raise ValueError("Division by 0")
            return A % B

        ### Comparison Operations
        elif op == 'CMP':

            # 00000LGE
            if A == B:
                return 0b00000001
            
            elif A > B:
                return 0b00000010

            elif A < B:
                return 0b00000100


        ### Bitwise Operations
        elif op == 'AND':
            return A & B

        elif op == 'OR':
            return A | B

        elif op == 'XOR':
            return A ^ B

        elif op == 'NOT':
            return 0b11111111 - A

        elif op == 'SHL':
            return A << B

        elif op == 'SHR':
            return A >> B

        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()


    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value


    def pc_increment(self, instruction):
        """
        Given an instruction, return the number PC must be incremented by 
        after that instruction has been run
        """
        
        # Use a mask with 
        mask = 0b11000000
        
        # Remove irrelevant information with mask
        operands = instruction & mask

        # Shift bits to remove trailing 0's
        operands = operands >> 6

        # Add one to account for the instruction itself
        return operands + 0b1


    def run(self):
        """Run the CPU."""
        
        self.reg[7] = 0xF4
        
        # After loading a program, we want to run it.
        running = True
        
        while running == True:
            
            instruction = self.ram_read(self.pc)
            self.ir = instruction
            
            # LDI 
            if instruction == 0b10000010:
                """
                LDI register immediate
                Set the value of a register to an integer.

                [command] = 0b10000010
                [register number]
                [immediate value]
                """

                

                register_num = self.ram_read(self.pc + 1)
                value = self.ram_read(self.pc + 2)

                ## Trouble shooting code
                # print("\nLDI")
                # print("PC\t", self.pc)
                # print("Reg\t" + ' R' + str(register_num))
                # print("Value\t", value)

                self.reg[register_num] = value
                self.pc += self.pc_increment(instruction)
            
            # PRN
            elif instruction == 0b01000111:
                """
                `PRN register` pseudo-instruction
                Print numeric value stored in the given register.

                [command] = 0b01000111
                [register number]
                """
                register_num = self.ram_read(self.pc + 1)
                
                print(self.reg[register_num])
                self.pc += self.pc_increment(instruction)

            # HLT
            elif instruction == 0b00000001:
                """
                `HLT`
                Halt the CPU (and exit the emulator).

                [command] = 0b00000001
                """
                running = False
            

            ### Stack Operations
            # PUSH
            elif instruction == 0b01000101:
                """
                `PUSH`
                Push the value in the given register on the stack.
                1. Decrement the `SP`.
                2. Copy the value in the given register to the address pointed to by `SP`.

                [command] = 01000101
                [register number]
                """
                # Step 1
                self.sp -= 1

                # Step 2
                register_num = self.ram_read(self.pc + 1)
                value = self.reg[register_num]
                self.ram_write(self.sp, value)
                
                self.pc += self.pc_increment(instruction)
            
            # POP
            elif instruction == 0b01000110:
                """
                `POP register`
                Pop the value at the top of the stack into the given register.
                1. Copy the value from the address pointed to by `SP` to the given register.
                2. Increment `SP`.

                [command] = 01000110
                [register number]
                """
                # Step 1
                value = self.ram_read(self.sp)

                register_num = self.ram_read(self.pc + 1)
                self.reg[register_num] = value
                
                # Step 2
                self.sp += 1

                self.pc += self.pc_increment(instruction)


            ### Subroutines
            # CALL
            elif instruction == 0b01010000:
                """
                `CALL register`

                Calls a subroutine (function) at the address stored in the register.

                1. The address of the ***instruction*** _directly after_ `CALL` is
                pushed onto the stack. This allows us to return to where we left off when the subroutine finishes executing.
                2. The PC is set to the address stored in the given register. We jump to that location in RAM and execute the first instruction 
                in the subroutine. The PC can move forward or backwards from its current location.

                [command] = 01010000
                [register number]
                """
                # Get address of next instruction
                return_address = self.pc + 2 
                
                # Push address onto memory stack
                self.sp -= 1
                self.ram_write(self.sp, return_address)


                # Get the address for our subroutine from the given register 
                # and re-assign PC to it
                register_num = self.ram_read(self.pc + 1)
                subroutine_PC = self.reg[register_num]
                self.pc = subroutine_PC

                
            # RET
            elif instruction == 0b00010001:
                """
                `RET`
                Return from subroutine.
                Pop the value from the top of the stack and store it in the `PC`.
                """
                # Pop the PC address we want to return to from the stack
                return_address = self.ram_read(self.sp)
                self.sp += 1
                
                # Re-assgin pc
                self.pc = return_address


            ### JUMP Instructions
            # JMP
            elif instruction == 0b01010100:
                """
                `JMP register`
                Jump to the address stored in the given register.
                Set the `PC` to the address stored in the given register.

                [command] = 01010100
                [register]
                """
                # Get address/index for where the desired PC value is stored
                register_num = self.ram_read(self.pc + 1)

                # Set PC to that value
                self.pc = self.reg[register_num]

            # JEQ
            elif instruction == 0b01010101:
                """
                `JEQ register`
                If `equal` flag is set (true), jump to the address stored in the given register.

                [command] = 01010101
                [register]
                """
                # Get address/index for where the desired PC value is stored
                register_num = self.ram_read(self.pc + 1)
                
                # Flag format is 00000LGE
                # Check if flag is set to "Equals"
                if self.fl & 0b00000001:
                    self.pc = self.reg[register_num]
                
                else:
                    self.pc += self.pc_increment(instruction)

            # JNE
            elif instruction == 0b01010110:
                """
                `JNE register`
                If `E` flag is clear (false, 0), jump to the address stored in the given
                register.

                [command] = 01010110
                [register]
                """
                # Get address/index for where the desired PC value is stored
                register_num = self.ram_read(self.pc + 1)

                # Flag format is 00000LGE
                # To do this bitwise, need to either shift bits then use XOR
                # Or use 2 bitwise comparisons (one for G and one for L)
                if self.fl != 0b00000001:
                    self.pc = self.reg[register_num]
                
                else:
                    self.pc += self.pc_increment(instruction)


            ### ALU Operations
            # ADD
            elif instruction == 0b10100000:
                """
                `ADD registerA registerB`
                Add the value in two registers and store the result in registerA.

                [command] = 10100000
                [register A]
                [Register B]
                """
                # 
                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)
                product = self.alu('ADD', register_num_A, register_num_B)
                
                self.reg[register_num_A] = product
                self.pc += self.pc_increment(instruction)
            
            # MUL
            elif instruction == 0b10100010:
                """
                `MUL registerA registerB`
                Multiply the values in two registers together and store the result in registerA.

                [command] = 10100010
                [register number A]
                [register number B]
                """
                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)
                product = self.alu('MUL', register_num_A, register_num_B)
                
                self.reg[register_num_A] = product
                self.pc += self.pc_increment(instruction)
            
            # SUB
            elif instruction == 0b10100001:
                """
                `SUB registerA registerB`

                Subtract the value in the second register from the first, storing the
                result in registerA.

                Machine code:
                ```
                10100001 00000aaa 00000bbb
                """
                pass
            
            # DIV
            elif instruction == 0b10100011:
                """
                `DIV registerA registerB`
                Divide the value in the first register by the value in the second,
                storing the result in registerA.
                If the value in the second register is 0, the system should print an
                error message and halt.

                Machine code:
                ```
                10100011 00000aaa 00000bbb
                """
                pass
            
            # MOD
            elif instruction == 0b10100100:
                """
                `MOD registerA registerB`

                [command] = 10100100
                [register number A]
                [register number B]
                """
            
                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)

                result = self.alu('MOD', register_num_A, register_num_B)

                self.reg[register_num_A] = result

                self.pc += self.pc_increment(instruction)

            # CMP
            elif instruction == 0b10100111:
                """
                CMP registerA registerB

                Compare the values in two registers.
                If they are equal, set the Equal E flag to 1, otherwise set it to 0.
                If registerA is less than registerB, set the Less-than L flag to 1, otherwise set it to 0.
                If registerA is greater than registerB, set the Greater-than G flag to 1, otherwise set it to 0.
                
                [command] = 10100111
                [register number A]
                [register number B]
                """

                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)

                # Flag format is 00000LGE
                new_flag = self.alu('CMP', register_num_A, register_num_B)

                # print("Before")
                # print("self.fl  ", self.fl, format(self.fl, ' 08b'))

                # print("\nNew flag ", new_flag, format(new_flag, ' 08b'))

                # use bitwise OR to set self.fl = new_flag
                #self.fl = self.fl | new_flag
                self.fl = new_flag
                
                # print("\nAFTER")
                # print("self.fl  ", self.fl, format(self.fl, ' 08b'))
                # return 

                ## Trouble shooting code
                # print('\nCMP')
                # print("PC\t", self.pc)
                # #print("Reg A", register_num_A, " Reg B", register_num_B)
                # #print("Reg A", format(register_num_A, '08b'), "Reg B", format(register_num_B, '08b'))
                # print("R" + str(register_num_A), 'vs.', 'R' + str(register_num_B))
                
                # print("LGE")
                # print(format(self.fl, '08b'))

                self.pc += self.pc_increment(instruction)
            
            # AND
            elif instruction == 0b10101000:
                """
                `AND registerA registerB`
                Bitwise-AND the values in registerA and registerB, then store the result in
                registerA.

                [command] = 
                [register number A]
                [register number B]
                """
                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)

                result = self.alu('AND', register_num_A, register_num_B)

                self.reg[register_num_A] = result

                self.pc += self.pc_increment(instruction)

            # OR
            elif instruction == 0b10101010:
                """
                `OR registerA registerB`

                [command] = 
                [register number A]
                [register number B]
                """

                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)

                result = self.alu('OR', register_num_A, register_num_B)

                self.reg[register_num_A] = result

                self.pc += self.pc_increment(instruction)
            
            # XOR
            elif instruction == 0b10101011:
                """
                `XOR registerA registerB`

                [command] = 10101011
                [register number A]
                [register number B]
                """
                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)

                result = self.alu('XOR', register_num_A, register_num_B)

                self.reg[register_num_A] = result

                self.pc += self.pc_increment(instruction)
                

            # NOT
            elif instruction == 0b01101001:
                """
                `NOT register`

                [command] = 01101001
                [register number A]
                """
                register_num_A = self.ram_read(self.pc + 1)

                # 3rd argument isn't used by the ALU for NOT
                # Can insert any valid register
                result = self.alu('NOT', register_num_A, register_num_A)

                self.reg[register_num_A] = result
                
                self.pc += self.pc_increment(instruction)

            # SHL
            elif instruction == 0b10101100:
                """
                `SHL registerA registerB`

                [command] = 10101100
                [register number A]
                [register number B]
                """
                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)

                result = self.alu('SHL', register_num_A, register_num_B)

                self.reg[register_num_A] = result

                self.pc += self.pc_increment(instruction)
                
            # SHR 
            elif instruction == 0b10101101:
                """
                `SHR registerA registerB`

                [command] = 10101101
                [register number A]
                [register number B]
                """
                register_num_A = self.ram_read(self.pc + 1)
                register_num_B = self.ram_read(self.pc + 2)

                result = self.alu('SHR', register_num_A, register_num_B)

                self.reg[register_num_A] = result

                self.pc += self.pc_increment(instruction)
                

                
