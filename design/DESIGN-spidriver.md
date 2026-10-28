# LCDDisplay through SPIDriver

Part of [LCDDisplay](OVERVIEW.md). Makes the module (an ILI9341 colour panel on a Raspberry Pi)
work through the SPIDriver interface of the SPIDriver2 project (its `design/` directory:
client interface, driver interface, BCM2835 driver), and tests it in RISC OS Pyromaniac
against an emulated display. The BCM2835 driver comes later; what this work finds that it
will need is recorded in SPIDriver2's BCM2835 driver design.

## Goal

LCDDisplay talks to the panel through SPIDriver (`SPID_*` SWIs), not by mapping the BCM2835
registers. The result is shown working in Pyromaniac, with the panel drawn in its GTK or
wxWidgets window, in the way the SSD1306 (IIC) display controller is.

## Decisions

All from the user, in the conversation which started this design.

- **Review is interactive**, not on a merge request.
- **The old code stays.** LCDDisplay is changed with `#ifdef ROOL_SPIDRIVER`, so that the
  existing register-level code still builds and works while the author is changing the
  module and this driver is experimental. Without `ROOL_SPIDRIVER` the module is as it was.
- **Code and design location.** Both are in this repository, on a branch (this is the
  author's repository, so never on `main`). The build under the RISC OS build environment
  (`Makefile,fe1`) is done on branch `robe-build`; this design is on `spidriver`, which is
  based on it. Constants from the ROOL source
  that are not in the build environment are used with `#ifdef ROOL_SOURCE #include ... #else
  #define ... #endif`.
- **The SPIDriverBCM2835 driver is left until later.** The module is first tested in
  Pyromaniac with an internal SPI driver and an emulated display. Anything found which the
  BCM2835 driver needs is filed in the SPIDriver design (see the last section).
- **The SPI side of the test is a fake bus in SPIDriver2** (answer to LQ1): the fake bus
  driver and the ILI9341 model are Python in the SPIDriver2 repository, first writing the
  frame to a file so tests can compare it. The GTK/wxWidgets viewer is Pyromaniac work, done
  after, once the model works. The fake bus is designed in SPIDriver2 (`design/`), since it is
  the first of its kind and other clients will use it.
- **Reset and backlight go through the GPIO and PWM modules** (answer to LQ2), so the
  module can run in Pyromaniac. They therefore need configuration: see LQ4.
- **The channel is chosen with a module command** for now (answer to LQ3), not a system
  variable or an automatic choice.
- **Polled transfers first.** DMA and the `Background` flag are not used.

Presented as proposals and not challenged (so taken as decisions):

- Under `ROOL_SPIDRIVER` the driver owns the SPI pins, the chip select and the
  data/command line. LCDDisplay keeps the panel reset and the backlight.

## Investigations

- **LI1 (done). Pyromaniac has no SPI support.** Its `pymods/driver` has IIC (with
  `iicinternal`, a registry of protocol-level device models configured by a string), GPIO,
  PWM devices and analogue devices, and nothing for SPI. The SPI driver in Pyromaniac does
  not exist yet, so "the internal SPI driver" is new work.
- **LI2 (done). How the SSD1306 is shown.** Three parts: a device model in `iicinternal`
  (`ssd1306.py`, 476 lines), a frame device (`graphicsimp/framedeviceimp/ssd1306.py`, which
  can also drive the real panel) and a viewer class in `graphicsimp/wxwidgetsimp`
  (`cls_ssd1306.py`, 127 lines), fed by a snapshot. `DeviceControls` (`docs/DEVICECONTROLS.md`)
  is the host-facing description of device state, with boolean and float grids; whether it has
  anything suited to a 320 x 240 colour image is not yet checked (LI3).
- **LI3 (open, during design). What Pyromaniac offers for showing a colour image from a
  device model**, and whether a PyModule can add a viewer without changing Pyromaniac's own
  GUI classes. Evidence: the `DeviceControls` and `wxwidgets`/`gtk` code.
- **LI4 (open, during design). What LCDDisplay needs besides SPI.** It maps the GPIO, PWM
  and clock-manager registers directly (reset on GPIO 27, backlight PWM on GPIO 18, pin
  function selection). Under Pyromaniac those registers do not exist, so the module's
  `map_registers` and `hw_init` cannot run there. Evidence: a read of `c/module` and
  Pyromaniac's `gpio.py` and `pwmdevices.py`.

## Open Questions

- **LQ4. How are the reset, backlight and (later) other ports configured?** Under
  `ROOL_SPIDRIVER` they go through the GPIO and PWM services, so the module needs to be told
  which GPIO port and pin is the reset, and which PWM device and output is the backlight (a
  non-BCM2835 board wires them differently). Proposal: module commands, as for the channel
  (LQ3's answer), each with a default of the Raspberry Pi wiring (reset GPIO 27, backlight
  PWM on GPIO 18): `*LCDDisplayChannel <name>`, `*LCDDisplayReset <port> <pin>`,
  `*LCDDisplayBacklight <device> <output>`. Is a module command the right form for all
  three, or should the pins also be readable from system variables so a boot sequence can
  set them without the module loaded?
- **LQ5. What is the GPIO and PWM service API to target?** Pyromaniac has the old GPIO module
  (SWI chunk `&58F80`, `GPIO_ReadData`, `GPIO_WriteMode` and so on, whose interface depends on
  the hardware) and a `PWMDevices` module (`Enumerate`, `Claim`, `Output...`, `Commit`). The
  real RISC OS the module runs on needs the same calls to exist. Which does the author
  expect (investigation LI4 will establish what each offers)?

## Findings for the BCM2835 driver

(None yet. Each thing learned here that the BCM2835 driver will need goes here and into
SPIDriver2's `design/DESIGN-bcm2835-driver.md` when it is settled.)

## Fake devices on a fake SPI bus

This is the open idea of the same name in SPIDriver2's `design/IDEAS.md`, which it would
answer. A driver registers a bus whose channels each have a Python
device model attached, as the Pyromaniac IIC module's internal devices do: the models are
named, and attached to a channel in the configuration by their device name and options. It
lets clients be tested against fake sensors, flash chips and displays with no hardware. The
LCDDisplay case is a fake display which receives commands and frames and is inspected or
screenshotted. Not yet designed: the model interface (bytes exchanged per transfer, with the
auxiliary line level so a display model can tell command from data, and the chip-select state
for `KeepCS` transactions), how channels are configured, and whether it replaces
`SPIDriverLoopback` or is built from it.
