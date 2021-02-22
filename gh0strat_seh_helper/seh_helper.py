__author__ = "tcontre - Br3akp0int"

"""
description: a simple ida python script that will create a code reference comment
             for all possible AddressOfHandler of tryBlock SEH entries.

"""
import os
import sys
import idaapi
import idautils
import idc


class FindXref:

    def __init__(self):
        self.needed_func_name = "___CxxFrameHandler"
        self.frmhdlr_xref= []
        self.MAX_SEARCH = 5
        self.try_block_map_entry_size = 0x14
        self.handler_type_size = 0x10
        return

    def find_xref_func(self, func_addr):
        """
        description: finding all xref address of the ___CxxFrameHandler
        """
        for addrs in idautils.XrefsTo(func_addr, flags=0):
            self.frmhdlr_xref.append(addrs.frm)
        return

    

    def parse_tryblock_addr_handler_entry(self, seh_init_addr, addr_, eh_func_info_addr):
        try_block_count = idaapi.get_dword(eh_func_info_addr + 4 * 3)
        if try_block_count >0x50:
            print ("[-] WARNING: too big tryblockCount!!\n")
            exit()
        else:
            n=0
            try_block_map_entry = idaapi.get_dword(eh_func_info_addr + 4 * 4)
            for i in range (0, try_block_count):
                handler_type_struct = idaapi.get_dword(try_block_map_entry + 4 * 4)
                handler_of_address = idaapi.get_dword(handler_type_struct + 4 * 3)
                print ("\t |-> ptryBlockMapStructAddr: {} tryBlockCount: {} \n\t\t |-> handlerTypeStructAddr: {} handlerOfAddress: {}\n".format(hex(try_block_map_entry),
                                                                                                                                                hex(try_block_count),
                                                                                                                                                hex(handler_type_struct),
                                                                                                                                                hex(handler_of_address)))

                #idaapi.add_cref(seh_init_addr, handler_of_address,dr_O)
                idc.update_extra_cmt(seh_init_addr, idc.E_PREV + n, "ehFuncInfoStructAddr: {} ptryBlockMapStructAddr: {} tryBlockCount: {} handlerTypeStructAddr: {} handlerOfAddres: {} ".format(hex(eh_func_info_addr),
                                                                                                                                                                                                  hex(try_block_map_entry),
                                                                                                                                                                                                  hex(try_block_count),
                                                                                                                                                                                                  hex(handler_type_struct),
                                                                                                                                                                                                  hex(handler_of_address)))
                n+=1
                #idc.set_cmt(addr_, "handlerAddres: 0x%08x" % handler_of_address,1)
                try_block_map_entry += self.try_block_map_entry_size
                
        return
    

    def find_ehfuncinfo_addr(self):
        for eh_addr in self.frmhdlr_xref:
            addr_ = eh_addr
            for i in range(0, self.MAX_SEARCH):
                addr_ = idc.prev_head(addr_)
                mnem = idc.print_insn_mnem(addr_)

                ### locate the ehfuncInfo address
                if mnem == 'mov' and idc.get_operand_type(addr_,0) == o_reg and idc.get_operand_type(addr_,1) == o_imm:
                    op1 = idc.print_operand(addr_, 0)
                    op2 = idc.print_operand(addr_, 1)
                    eh_func_info_addr = int(op2.replace("offset stru_",""),16)
                    
                    ### locate the ptryBlockMapAddr
                    for ad in idautils.XrefsTo(addr_, flags=0):
                        seh_init_addr = ad.frm
                    print("[+] seh_frame_addr: {} ehFuncInfo_struct_addr: {}\n------------------------------------------------------------------".format(hex(addr_),hex(eh_func_info_addr)))

                    ### locate the xref of the _cxxframehandler ehfuncinfo
                    self.parse_tryblock_addr_handler_entry(seh_init_addr, addr_, eh_func_info_addr)
        return

    def enum_func(self):

        ### iterate to all functions of the malware
        ea = here()
        func_addr = 0
        seg_start = idc.get_segm_start(ea)
        seg_end = idc.get_segm_end(ea)
        for func_addr in idautils.Functions(seg_start, seg_end):
            func_name = idc.get_func_name(func_addr)
            if func_name == self.needed_func_name:
                print("[+] STATUS: Found Needed Function -> {} {}".format(hex(func_addr), func_name))
                break
            else:
                pass
                #print("[-] STATUS: Skipped this Function -> {} {}".format(hex(func_addr),func_name))

        self.find_xref_func(func_addr)

        ### find the ehFuncInfo Address which is the mov address before the jmp to ___CxxFrameHandler
        ### .text:00407B60                 mov     eax, offset stru_408928
        ### .text:00407B65                 jmp     ___CxxFrameHandler

        self.find_ehfuncinfo_addr()

        return
    


def main():
    """
    description:
    locate the xref for all __CxxFramehandler Function and anotate all the AddressOfhandlers of that SEH
    """

    fx = FindXref()
    fx.enum_func()
    
    return


if __name__ == "__main__":
    main()
