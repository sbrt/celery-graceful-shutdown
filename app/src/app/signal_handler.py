import signal

def chain_signal_handler_to_previous(signum, signal_handler):
    original_handler = signal.getsignal(signum)

    def combined_signal_handler(signum, frame):
        signal_handler(signum, frame)
        if callable(original_handler):
            original_handler(signum, frame)
    signal.signal(signum, combined_signal_handler)

if __name__ == "__main__":
    def my_signal_handler(signum, frame):
        print("Custom handler called for signal:", signum)

    # does NOT interrupt in terminal
    # signal.signal(signal.SIGINT, my_signal_handler)

    # does interrupt in terminal
    chain_signal_handler_to_previous(signal.SIGINT, my_signal_handler)
    chain_signal_handler_to_previous(signal.SIGTERM, my_signal_handler)

    # Example to keep the program running to test signal handling
    print("Press Ctrl+C to trigger the signal.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Program interrupted.")
