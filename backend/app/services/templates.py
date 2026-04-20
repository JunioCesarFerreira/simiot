"""Seed firmware tree installed in every new project."""

_MAIN_C = '''#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "simiot";

void app_main(void)
{
    ESP_LOGI(TAG, "Hello from SimIoT!");
    int counter = 0;
    while (1) {
        ESP_LOGI(TAG, "tick %d", counter++);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
'''

_ROOT_CMAKE = '''cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(simiot_firmware)
'''

_MAIN_CMAKE = 'idf_component_register(SRCS "main.c" INCLUDE_DIRS ".")\n'


DEFAULT_FIRMWARE_FILES: dict[str, str] = {
    "CMakeLists.txt": _ROOT_CMAKE,
    "main/CMakeLists.txt": _MAIN_CMAKE,
    "main/main.c": _MAIN_C,
}
