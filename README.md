# SED1115 Pair Project

Daniel Chen and Cailan Ferguson

# todo:

-   rc filter
-   if one disconnect and chooses a duty cycle then it needs ot communicate it back

# Running the project

The project is structured in such a way that it may be run with or without a pico.
There are three different modes of operation:

-   loopback: Runs locally in a single process with a handler that internally simulates
    messages being transmitted and received. Capable of simulating dropped packets as well.
-   uart: Runs on a micropython device and uses UART to transmit messages.
-   pipe: Runs on a desktop device and uses two processes with python pipes to communicate.

## Running on a pico

Load all of the files in the `src/` directory onto the pico, then update
the configuration in `src/config.py`:

```py
TARGET = "micropython" # to enable micropython-specific libraries
MODE = "uart" # to enable interdevice uart
```

`"loopback"` mode is also able to be run on picos.

Execute the `main.py` file.

## Running locally

Modify the `src/config.py` file:

```py
TARGET = "python"
MODE = "pipe" # or loopback
```

Execute the `main.py` file.

## Executing tests

From project directory:

```
$ python3 -m unittest test/test_<test>.py
```
