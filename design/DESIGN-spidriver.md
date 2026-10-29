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
- **The SPI side of the test is an emulated bus in SPIDriver2** (answer to LQ1): the emulated bus
  driver and the ILI9341 model are Python in the SPIDriver2 repository, first writing the
  frame to a file so tests can compare it. The GTK/wxWidgets viewer is Pyromaniac work, done
  after, once the model works. The emulated bus is designed in SPIDriver2 (`design/`), since it is
  the first of its kind and other clients will use it.
- **Reset and backlight go through the GPIO and PWM modules** (answer to LQ2), so the
  module can run in Pyromaniac. They therefore need configuration: see LQ4.
- **The channel is chosen with a module command** for now (answer to LQ3), not a system
  variable or an automatic choice.
- **The pins are configured by module commands** (answer to LQ4), with the Raspberry Pi
  wiring as defaults (reset GPIO 27, backlight GPIO 18): `*LCDDisplayChannel <name>`,
  `*LCDDisplayReset <pin>` and `*LCDDisplayBacklight ...`, and are also readable from
  system variables so a boot sequence can set them without the module loaded. (The exact
  commands are for the plan.)
- **Reset goes through the GPIO module** (the old per-pin interface, which the author
  regards as well defined and widely used). **The backlight PWM does not move to
  `PWMDevices` yet** (answer to LQ5): it will be controlled differently, so for now a define
  disables the PWM code (LQ6).
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
- **LI4 (done). What LCDDisplay needs besides SPI, and what the services offer.** The module
  touches the hardware directly in these places: the SPI0 registers and DMA (`c/lcd`, the part
  replaced by SPIDriver); the GPIO function-select registers for pins 7 to 11 (SPI) and 18
  (PWM), and the direction of the data/command pin 25 and the reset pin 27 (`hw_init` in
  `c/module`); the data/command pin (`lcd_command`), the chip select 8 and the reset 27
  (`lcd_reset`) in `c/lcd`; and the backlight PWM and its clock manager (`hw_init`, `module_final`
  in `c/module`, `lcd_set_backlight`, `lcd_backlight_start` and `lcd_backlight_stop` in `c/lcd`).
  The GPIO module (SWI chunk `&58F80`) provides per-pin calls: `GPIO_ReadData` (R0 = pin, returns
  the level or -1), `GPIO_WriteData` (R0 = pin, R1 = level), `GPIO_WriteOE` (R0 = pin, R1 = 0 for
  output) and `GPIO_WriteMode`, which is enough for the reset line. `PWMDevices` is new and its
  use for the backlight is not decided (LQ5).

- **LI5 (done). Which controller the panel is.** The module's header comments say ILI9341, but
  the initialisation table in `c/lcd` uses the ST7789 register names (PORCH, GCTRL, VCOMS, LCMCTL,
  VDVVRHEN, VRHS, VDVS, FRCTRL2, PWCTRL1, PGAMCTRL, NGAMCTRL). The generic commands (sleep out,
  display on, the window, memory write, memory access control and pixel format) are common to
  both. The emulated model is registered as `st7789` and `ili9341`. Not verified against the
  hardware: the author should confirm which chip the panel has.

## Open Questions

- **LQ6. What is the name of the define which disables the backlight PWM?** Proposal:
  `LCDDISPLAY_NO_PWM`, set in the makefile for a build which has no way to control the
  backlight. With it, `lcd_set_backlight` keeps the brightness (so `*LCDDisplayBrightness`,
  fade and the state all work) but touches no hardware, and `hw_init`/`module_final` skip the
  PWM and clock setup. `ROOL_SPIDRIVER` alone would not imply it, so a Raspberry Pi build can
  use SPIDriver and the register-level PWM together until `PWMDevices` is used.

## Findings for the BCM2835 driver

(None yet. Each thing learned here that the BCM2835 driver will need goes here and into
SPIDriver2's `design/DESIGN-bcm2835-driver.md` when it is settled.)

## Emulated devices on an emulated SPI bus

Designed in SPIDriver2 (`design/DESIGN-emulated-devices.md`), since it is the first emulated
bus and other clients will use it. For this module it provides the SPI channel with an
emulated ILI9341 display, which receives the commands and frames and writes the picture to a
file.
