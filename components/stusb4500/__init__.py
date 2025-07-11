import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor, i2c, text_sensor
from esphome import core, pins
from esphome.core import TimePeriod, TimePeriodSeconds
from esphome import automation
from esphome.automation import maybe_simple_id

from esphome.const import (
    CONF_ID,
)

CONF_ALERT_PIN = "alert_pin"
CONF_FLASH_NVM = "flash_nvm"
CONF_DEFAULT_NVM = "default_nvm"
CONF_SNK_PDO_NUMB = "snk_pdo_numb"
CONF_V_SNK_PDO2 = "v_snk_pdo2"
CONF_V_SNK_PDO3 = "v_snk_pdo3"
CONF_I_SNK_PDO1 = "i_snk_pdo1"
CONF_I_SNK_PDO2 = "i_snk_pdo2"
CONF_I_SNK_PDO3 = "i_snk_pdo3"
CONF_I_SNK_PDO_FLEX = "i_snk_pdo_flex"
CONF_SHIFT_VBUS_HL1 = "shift_vbus_hl1"
CONF_SHIFT_VBUS_LL1 = "shift_vbus_ll1"
CONF_SHIFT_VBUS_HL2 = "shift_vbus_hl2"
CONF_SHIFT_VBUS_LL2 = "shift_vbus_ll2"
CONF_SHIFT_VBUS_HL3 = "shift_vbus_hl3"
CONF_SHIFT_VBUS_LL3 = "shift_vbus_ll3"
CONF_VBUS_DISCH_TIME_TO_0V = "vbus_disch_time_to_0v"
CONF_VBUS_DISCH_TIME_TO_PDO = "vbus_disch_time_to_pdo"
CONF_VBUS_DISCH_DISABLE = "vbus_disch_disable"
CONF_USB_COMM_CAPABLE = "usb_comms_capable"
CONF_SNK_UNCONS_POWER = "snk_uncons_power"
CONF_REQ_SRC_CURRENT = "req_src_current"
CONF_POWER_OK_CFG = "power_ok_cfg"
CONF_POWER_ONLY_ABOVE_5V = "power_only_above_5v"
CONF_GPIO_CFG = "gpio_cfg"

CODEOWNERS = ["@mikelawrence"]
DEPENDENCIES = ["i2c"]
MULTI_CONF = True

stusb4500_ns = cg.esphome_ns.namespace("stusb4500")
STUSB4500Hub = stusb4500_ns.class_(
    "STUSB4500Hub", cg.Component, i2c.I2CDevice
)

CONF_STUSB4500_HUB_ID = "stusb4500_hub_id"

PowerOkConfig = stusb4500_ns.enum("PowerOkConfig")
POWER_OK_CONFIG = {
    "CONFIGURATION_1": PowerOkConfig.CONFIGURATION_1,
    "CONFIGURATION_2": PowerOkConfig.CONFIGURATION_2,
    "CONFIGURATION_3": PowerOkConfig.CONFIGURATION_3,
}

GPIOConfig = stusb4500_ns.enum("GPIOConfig")
GPIO_CONFIG = {
    "SW_CTRL_GPIO": GPIOConfig.SW_CTRL_GPIO,
    "ERROR_RECOVERY": GPIOConfig.ERROR_RECOVERY,
    "DEBUG": GPIOConfig.DEBUG,
    "SINK_POWER": GPIOConfig.SINK_POWER,
}


def validate_pdo_voltage(value):
    value = float(value)
    rvalue = round(value * 20.0) / 20.0
    if rvalue != value:
        raise cv.Invalid("PDO voltage must be a multiple of 0.05V")
    return value


def validate_pdo_current(value):
    value = float(value)
    rvalue = round(value * 4.0) / 4.0
    if rvalue != value:
        raise cv.Invalid("PDO current must be a multiple of 0.25 A")
    if value == 0.25:
        raise cv.Invalid("PDO current cannot be 0.25 A")
    if value == 3.25:
        raise cv.Invalid("PDO current cannot be 3.25 A")
    if value == 3.75:
        raise cv.Invalid("PDO current cannot be 3.75 A")
    return value


def validate_pdo_flex_current(value):
    value = float(value)
    rvalue = round(value * 100.0) / 100.0
    if rvalue != value:
        raise cv.Invalid("PDO Flex current must be a multiple of 0.01 A")
    return value


def validate_disch_time_0v(value):
    value = cv.positive_time_period_milliseconds(value).total_milliseconds
    rvalue = int(round(float(value) / 84.0) / 84)
    if rvalue != value:
        raise cv.Invalid("VBUS Discharge Time to 0V must be a multiple of 84 ms")
    return value


def validate_disch_time_pdo(value):
    value = cv.positive_time_period_milliseconds(value).total_milliseconds
    rvalue = int(round(value * 24.0) / 24.0)
    if rvalue != value:
        raise cv.Invalid("VBUS Discharge time to PDO must be a multiple of 24 ms")
    return value

HUB_CHILD_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_STUSB4500_HUB_ID): cv.use_id(STUSB4500Hub),
    }
)

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(STUSB4500Hub),
            cv.Optional(CONF_ALERT_PIN): pins.internal_gpio_input_pin_schema,
            cv.Optional(CONF_FLASH_NVM): cv.boolean,
            cv.Optional(CONF_DEFAULT_NVM): cv.boolean,
            cv.Optional(CONF_SNK_PDO_NUMB): cv.int_range(min=1, max=3),
            cv.Optional(CONF_V_SNK_PDO2): cv.All(
                cv.voltage,
                cv.Range(min=5.0, max=20.0),
                validate_pdo_voltage,
            ),
            cv.Optional(CONF_V_SNK_PDO3): cv.All(
                cv.voltage,
                cv.Range(min=5.0, max=20.0),
                validate_pdo_voltage,
            ),
            cv.Optional(CONF_I_SNK_PDO1): cv.All(
                cv.current,
                cv.Range(min=0.0, max=5.0),
                validate_pdo_current,
            ),
            cv.Optional(CONF_I_SNK_PDO2): cv.All(
                cv.current,
                cv.Range(min=0.0, max=5.0),
                validate_pdo_current,
            ),
            cv.Optional(CONF_I_SNK_PDO3): cv.All(
                cv.current,
                cv.Range(min=0.0, max=5.0),
                validate_pdo_current,
            ),
            cv.Optional(CONF_I_SNK_PDO_FLEX): cv.All(
                cv.current,
                cv.Range(min=0.01, max=5.0),
                validate_pdo_flex_current,
            ),
            cv.Optional(CONF_SHIFT_VBUS_HL1): cv.All(
                cv.percentage, cv.Range(min=0.01, max=0.15)
            ),
            cv.Optional(CONF_SHIFT_VBUS_LL1): cv.All(
                cv.percentage, cv.Range(min=0.01, max=0.15)
            ),
            cv.Optional(CONF_SHIFT_VBUS_HL2): cv.All(
                cv.percentage, cv.Range(min=0.01, max=0.15)
            ),
            cv.Optional(CONF_SHIFT_VBUS_LL2): cv.All(
                cv.percentage, cv.Range(min=0.01, max=0.15)
            ),
            cv.Optional(CONF_SHIFT_VBUS_HL3): cv.All(
                cv.percentage, cv.Range(min=0.01, max=0.15)
            ),
            cv.Optional(CONF_SHIFT_VBUS_LL3): cv.All(
                cv.percentage, cv.Range(min=0.01, max=0.15)
            ),
            cv.Optional(CONF_VBUS_DISCH_TIME_TO_0V): cv.All(
                cv.positive_time_period_milliseconds,
                cv.Range(
                    min=core.TimePeriod(milliseconds=84),
                    max=core.TimePeriod(milliseconds=1260),
                ),
                validate_disch_time_pdo,
            ),
            cv.Optional(CONF_VBUS_DISCH_TIME_TO_PDO): cv.All(
                cv.positive_time_period_milliseconds,
                cv.Range(
                    min=core.TimePeriod(milliseconds=24),
                    max=core.TimePeriod(milliseconds=360),
                ),
                validate_disch_time_pdo,
            ),
            cv.Optional(CONF_VBUS_DISCH_DISABLE): cv.boolean,
            cv.Optional(CONF_POWER_OK_CFG): cv.enum(
                POWER_OK_CONFIG, upper=True, space="_"
            ),
            cv.Optional(CONF_GPIO_CFG): cv.enum(GPIO_CONFIG, upper=True, space="_"),
            cv.Optional(CONF_USB_COMM_CAPABLE): cv.boolean,
            cv.Optional(CONF_SNK_UNCONS_POWER): cv.boolean,
            cv.Optional(CONF_REQ_SRC_CURRENT): cv.boolean,
            cv.Optional(CONF_POWER_ONLY_ABOVE_5V): cv.boolean,
        }
    )
    .extend(i2c.i2c_device_schema(0x28))
    .extend(cv.COMPONENT_SCHEMA)
)


FINAL_VALIDATE_SCHEMA = i2c.final_validate_device_schema(
    "stusb4500", max_frequency="400khz"
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)

    if CONF_ALERT_PIN in config:
        cg.add(var.set_alert_pin(await cg.gpio_pin_expression(config[CONF_ALERT_PIN])))
    if CONF_FLASH_NVM in config:
        cg.add(var.set_flash_nvm(config[CONF_FLASH_NVM]))
    if CONF_DEFAULT_NVM in config:
        cg.add(var.set_default_nvm(config[CONF_DEFAULT_NVM]))
    if CONF_SNK_PDO_NUMB in config:
        cg.add(var.set_snk_pdo_numb(config[CONF_SNK_PDO_NUMB]))
    if CONF_V_SNK_PDO2 in config:
        cg.add(var.set_v_snk_pdo2(config[CONF_V_SNK_PDO2]))
    if CONF_V_SNK_PDO3 in config:
        cg.add(var.set_v_snk_pdo3(config[CONF_V_SNK_PDO3]))
    if CONF_I_SNK_PDO1 in config:
        cg.add(var.set_i_snk_pdo1(config[CONF_I_SNK_PDO1]))
    if CONF_I_SNK_PDO2 in config:
        cg.add(var.set_i_snk_pdo2(config[CONF_I_SNK_PDO2]))
    if CONF_I_SNK_PDO3 in config:
        cg.add(var.set_i_snk_pdo3(config[CONF_I_SNK_PDO3]))
    if CONF_I_SNK_PDO_FLEX in config:
        cg.add(var.set_i_snk_pdo_flex(config[CONF_I_SNK_PDO_FLEX]))
    if CONF_SHIFT_VBUS_HL1 in config:
        cg.add(var.set_shift_vbus_hl1(config[CONF_SHIFT_VBUS_HL1]))
    if CONF_SHIFT_VBUS_LL1 in config:
        cg.add(var.set_shift_vbus_ll1(config[CONF_SHIFT_VBUS_LL1]))
    if CONF_SHIFT_VBUS_HL2 in config:
        cg.add(var.set_shift_vbus_hl2(config[CONF_SHIFT_VBUS_HL2]))
    if CONF_SHIFT_VBUS_LL2 in config:
        cg.add(var.set_shift_vbus_ll2(config[CONF_SHIFT_VBUS_LL2]))
    if CONF_SHIFT_VBUS_HL3 in config:
        cg.add(var.set_shift_vbus_hl3(config[CONF_SHIFT_VBUS_HL3]))
    if CONF_SHIFT_VBUS_LL3 in config:
        cg.add(var.set_shift_vbus_ll3(config[CONF_SHIFT_VBUS_LL3]))
    if CONF_VBUS_DISCH_TIME_TO_0V in config:
        cg.add(var.set_vbus_disch_time_to_0v(config[CONF_VBUS_DISCH_TIME_TO_0V]))
    if CONF_VBUS_DISCH_TIME_TO_PDO in config:
        cg.add(var.set_vbus_disch_time_to_pdo(config[CONF_VBUS_DISCH_TIME_TO_PDO]))
    if CONF_VBUS_DISCH_DISABLE in config:
        cg.add(var.set_vbus_disch_disable(config[CONF_VBUS_DISCH_DISABLE]))
    if CONF_POWER_OK_CFG in config:
        cg.add(var.set_power_ok_cfg(config[CONF_POWER_OK_CFG]))
    if CONF_GPIO_CFG in config:
        cg.add(var.set_gpio_cfg(config[CONF_GPIO_CFG]))
    if CONF_USB_COMM_CAPABLE in config:
        cg.add(var.set_usb_comm_capable(config[CONF_USB_COMM_CAPABLE]))
    if CONF_SNK_UNCONS_POWER in config:
        cg.add(var.set_snk_uncons_power(config[CONF_SNK_UNCONS_POWER]))
    if CONF_REQ_SRC_CURRENT in config:
        cg.add(var.set_req_src_current(config[CONF_REQ_SRC_CURRENT]))
    if CONF_POWER_ONLY_ABOVE_5V in config:
        cg.add(var.set_power_only_above_5v(config[CONF_POWER_ONLY_ABOVE_5V]))


# Actions
TurnGpioOn = stusb4500_ns.class_("TurnGpioOn", automation.Action)
TurnGpioOff = stusb4500_ns.class_("TurnGpioOff", automation.Action)

STUSB4500_ACTION_SCHEMA = maybe_simple_id(
    {
        cv.Required(CONF_ID): cv.use_id(STUSB4500Hub),
    }
)


@automation.register_action(
    "stusb4500.turn_gpio_on", TurnGpioOn, STUSB4500_ACTION_SCHEMA
)
@automation.register_action(
    "stusb4500.turn_gpio_off", TurnGpioOff, STUSB4500_ACTION_SCHEMA
)
async def stusb4500_fan_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    return cg.new_Pvariable(action_id, template_arg, paren)
