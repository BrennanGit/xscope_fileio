#We assume that the Xscope FileIO Python library has been installed via pip beforehand and is available to import. Please see readme for instuctions.
import numpy as np
import xscope_fileio
import os, sys
import xtagctl
import contextlib
import random, string
from compare_bins import analyse_error_rate
from contextlib import redirect_stdout
import io


@contextlib.contextmanager
def cd(path):
    CWD = os.getcwd()
    os.mkdir(path)
    os.chdir(path)
    yield
    os.chdir(CWD)


def run_throughput(size_mb):
    tmpdirname = 'tmp_throughput_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    test_dir = os.path.dirname(os.path.realpath(__file__)) + "/" + tmpdirname
    with cd(test_dir):
        ref = np.random.randint(256, size=(size_mb * 1024 * 1024)).astype(np.uint8)
        ref.tofile("throughput_ref.bin")


        f = io.StringIO()
        with redirect_stdout(f):
            with xtagctl.acquire("XCORE-AI-EXPLORER", timeout=10) as adapter_id:
                firmware_xe = test_dir + "/../../examples/throughput_c/fileio_test.xe"
                xscope_fileio.run_on_target(adapter_id, firmware_xe, use_xsim=False)

        byte_array = []
        for line in f.getvalue().splitlines():
            cleaned_line = line.replace("[DEVICE] ", "")
            print(cleaned_line)
            items = cleaned_line.split(" ")
            if items[0][0:2] == "0x":
                for item in items:
                    if item[0:2] == "0x":
                        byte_array.append(int(item, 0))


        stdo_vals = numpy.array(byte_array, dtype=np.uint8)
        stdo_vals.tofile("throughput_stdo.bin")

        dut = np.fromfile("throughput_dut.bin", dtype=np.uint8)

        equal = np.array_equal(ref, dut)
        if not equal:
            analyse_error_rate(ref, dut)
            assert 0

    print("PASS")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        size_mb = int(sys.argv[1])
    else:
        size_mb =  30
    run_throughput(size_mb)