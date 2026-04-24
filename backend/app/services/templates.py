"""Seed firmware tree installed in every new project."""

_MAIN_C = '''#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_eth.h"
#include "esp_eth_driver.h"
#include "mqtt_client.h"

static const char *TAG = "simiot";
static EventGroupHandle_t net_evt;
static const int GOT_IP_BIT = BIT0;
static esp_mqtt_client_handle_t mqtt_client = NULL;

static void eth_event_handler(void *arg, esp_event_base_t base,
                              int32_t id, void *data)
{
    switch (id) {
    case ETHERNET_EVENT_START:
        ESP_LOGI(TAG, "ethernet started");
        break;
    case ETHERNET_EVENT_CONNECTED:
        ESP_LOGI(TAG, "ethernet link up");
        break;
    case ETHERNET_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "ethernet link down");
        break;
    case ETHERNET_EVENT_STOP:
        ESP_LOGI(TAG, "ethernet stopped");
        break;
    default:
        break;
    }
}

static void got_ip_handler(void *arg, esp_event_base_t base,
                           int32_t id, void *data)
{
    ip_event_got_ip_t *event = (ip_event_got_ip_t *)data;
    ESP_LOGI(TAG, "got ip " IPSTR " gw " IPSTR,
             IP2STR(&event->ip_info.ip), IP2STR(&event->ip_info.gw));
    xEventGroupSetBits(net_evt, GOT_IP_BIT);
}

static void mqtt_event_handler(void *arg, esp_event_base_t base,
                               int32_t id, void *data)
{
    switch (id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "mqtt connected");
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "mqtt disconnected");
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGE(TAG, "mqtt error");
        break;
    default:
        break;
    }
}

static void ethernet_start(void)
{
    esp_netif_config_t netif_cfg = ESP_NETIF_DEFAULT_ETH();
    esp_netif_t *netif = esp_netif_new(&netif_cfg);

    eth_mac_config_t mac_cfg = ETH_MAC_DEFAULT_CONFIG();
    eth_phy_config_t phy_cfg = ETH_PHY_DEFAULT_CONFIG();
    phy_cfg.phy_addr = 1;
    phy_cfg.reset_gpio_num = -1;

    esp_eth_mac_t *mac = esp_eth_mac_new_openeth(&mac_cfg);
    esp_eth_phy_t *phy = esp_eth_phy_new_dp83848(&phy_cfg);

    esp_eth_config_t config = ETH_DEFAULT_CONFIG(mac, phy);
    esp_eth_handle_t eth = NULL;
    ESP_ERROR_CHECK(esp_eth_driver_install(&config, &eth));
    ESP_ERROR_CHECK(esp_netif_attach(netif, esp_eth_new_netif_glue(eth)));

    ESP_ERROR_CHECK(esp_event_handler_register(
        ETH_EVENT, ESP_EVENT_ANY_ID, eth_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(
        IP_EVENT, IP_EVENT_ETH_GOT_IP, got_ip_handler, NULL));

    ESP_ERROR_CHECK(esp_eth_start(eth));
}

void app_main(void)
{
    ESP_LOGI(TAG, "simiot boot");

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    net_evt = xEventGroupCreate();

    ethernet_start();

    ESP_LOGI(TAG, "waiting for IP...");
    xEventGroupWaitBits(net_evt, GOT_IP_BIT, pdFALSE, pdTRUE, portMAX_DELAY);

    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = "mqtt://10.0.2.2:1883",
    };
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    ESP_ERROR_CHECK(esp_mqtt_client_register_event(
        mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL));
    ESP_ERROR_CHECK(esp_mqtt_client_start(mqtt_client));

    int counter = 0;
    char payload[64];
    while (1) {
        snprintf(payload, sizeof(payload), "{\\"tick\\":%d}", counter);
        int msg_id = esp_mqtt_client_publish(
            mqtt_client, "simiot/hello", payload, 0, 1, 0);
        ESP_LOGI(TAG, "publish tick=%d msg_id=%d", counter, msg_id);
        counter++;
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}
'''

_ROOT_CMAKE = '''cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(simiot_firmware)
'''

_MAIN_CMAKE = '''idf_component_register(SRCS "main.c"
                       INCLUDE_DIRS "."
                       REQUIRES nvs_flash esp_netif esp_event esp_eth mqtt)
'''

_SDKCONFIG_DEFAULTS = '''# Enable the OpenEth virtual Ethernet MAC used by QEMU.
CONFIG_ETH_USE_OPENETH=y

# MQTT + TCP/IP + Ethernet pushes the app past the default 1 MB partition.
CONFIG_PARTITION_TABLE_SINGLE_APP_LARGE=y
'''


DEFAULT_FIRMWARE_FILES: dict[str, str] = {
    "CMakeLists.txt": _ROOT_CMAKE,
    "main/CMakeLists.txt": _MAIN_CMAKE,
    "main/main.c": _MAIN_C,
    "sdkconfig.defaults": _SDKCONFIG_DEFAULTS,
}
