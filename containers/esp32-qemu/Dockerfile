FROM espressif/idf:release-v5.4

# Install the Espressif QEMU fork (xtensa flavor) via idf_tools.
# The base image's entrypoint already puts installed tools on PATH.
RUN python "$IDF_PATH/tools/idf_tools.py" install qemu-xtensa

WORKDIR /project

# Default command: boot the firmware already built under /project in QEMU,
# routing the guest's UART to this container's stdout.
CMD ["idf.py", "qemu"]
