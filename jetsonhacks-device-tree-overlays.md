# Device Tree Overlays on Jetson - JetsonHacks Article Summary

**Source:** https://jetsonhacks.com/2025/04/07/device-tree-overlays-on-jetson-scary-but-fun/

## Key Concepts

### Device Tree Basics
- **Device Tree**: Hardware layout map that tells the Linux kernel where hardware components reside
- **Device Tree Overlay (.dtbo)**: Allows modifying the base device tree without altering the original
- Base device tree is in `.dts` format, compiled into `.dtb` file by Device Tree compiler (`dtc`)

### GPIO Configuration
- By default in JetPack 6.2, GPIO is input-only  
- Overlays can enable input/output for specific pins
- Sample overlay structure for pin configuration:

```dts
hdr40-pin7 {
  nvidia,pins = "soc_gpio59_pac6";
  nvidia,tristate = ;
  nvidia,enable-input = ;
  nvidia,pull = ;
};
```

### Tools and Resources
- `jetson-io` utility for configuring expansion header
- Pinmux spreadsheet for detailed signal mapping
- Linux kernel source headers for pin references

### Compilation and Usage
1. Compile `.dts` to `.dtbo`: `dtc -I dts -O dtb -o overlay.dtbo overlay.dts`
2. Copy to boot overlays directory: `/boot/firmware/overlays/`
3. Add to `/boot/firmware/config.txt`: `dtoverlay=overlay`
4. Reboot to apply changes

### Safety Notes
- Device tree configuration can seem complex but components are relatively simple
- Careful testing recommended to avoid system instability  
- Refer to specific Jetson model's pinout documentation
- Each overlay should be tested individually

## PIN 15 (GPIO 433) Implementation
Created device tree overlay file `pin15-gpio433.dts` with:
- Physical PIN 15 mapping to GPIO 433
- Proper Tegra234 GPIO configuration
- Input/Output capability enabled
- Pull-down resistor configuration
- Debounce settings for reliable operation

### Usage Instructions
1. Compile: `dtc -I dts -O dtb -o pin15-gpio433.dtbo pin15-gpio433.dts`
2. Install: `sudo cp pin15-gpio433.dtbo /boot/firmware/overlays/`
3. Enable: Add `dtoverlay=pin15-gpio433` to `/boot/firmware/config.txt`
4. Reboot system to apply changes