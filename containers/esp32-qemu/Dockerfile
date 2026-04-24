FROM espressif/idf:release-v5.4

# Install the Espressif QEMU fork (xtensa flavor) via idf_tools.
# The base image's entrypoint already puts installed tools on PATH.
RUN python "$IDF_PATH/tools/idf_tools.py" install qemu-xtensa

# Diagnostic: dump the installed qemu version and the full device list so we
# can see exactly which network devices this binary exposes.
RUN bash -lc '. "$IDF_PATH/export.sh" >/dev/null && \
              echo "=== qemu binary ===" && which qemu-system-xtensa && \
              echo "=== qemu version ===" && qemu-system-xtensa --version && \
              echo "=== machines ===" && qemu-system-xtensa -machine help && \
              echo "=== all devices ===" && qemu-system-xtensa -device help 2>&1'

WORKDIR /project

COPY simiot-qemu-runner.py /usr/local/bin/simiot-qemu-runner
RUN chmod +x /usr/local/bin/simiot-qemu-runner

# Default command: boot the firmware already built under /project in QEMU,
# routing the guest's UART to this container's stdout.
CMD ["simiot-qemu-runner"]
