import sys
import multiprocessing

if __name__ == "__main__":
    from three_d_fin import processing

    multiprocessing.freeze_support()
    sys.exit(processing.launch_application())
