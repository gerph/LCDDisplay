# LCDDisplay

A module which drives an ILI9341 colour panel (320 x 240, 16 bits a pixel) on a Raspberry
Pi.

## Goal of the current work

Make the module work through the SPIDriver interface (SPIDriver2 project), keeping the
existing register-level code under a conditional so that it is not disturbed while it is
being changed, and show it working in RISC OS Pyromaniac.

## Designs

- [LCDDisplay through SPIDriver](DESIGN-spidriver.md) - decisions, investigations and open
  questions.
