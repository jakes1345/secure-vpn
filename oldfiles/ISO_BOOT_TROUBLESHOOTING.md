# PhazeOS ISO Boot Troubleshooting

## Current Status
- ✅ ISO file is valid (5.0GB, bootable ISO 9660)
- ✅ QEMU is running with KVM acceleration
- ⚠️ Boot hangs at ":: Triggering uevents..."

## Possible Issues

### 1. Boot Menu Not Visible
Arch Linux ISOs have a boot menu. Try:
- **Press a key** when QEMU window appears (before it hangs)
- Look for boot menu options
- Select "Boot Arch Linux (x86_64)" or similar

### 2. ISO Takes Very Long Time
Large ISOs (5GB with KDE Plasma) can take 10-15 minutes on first boot:
- The "Triggering uevents" stage can legitimately take 5+ minutes
- Be patient - let it run for at least 15 minutes

### 3. ISO Build Issue
The ISO might have issues. Check:
```bash
# Verify ISO structure
file phazeos-build/out/archlinux-2025.12.08-x86_64.iso
isoinfo -d -i phazeos-build/out/archlinux-2025.12.08-x86_64.iso
```

### 4. QEMU Configuration
Try different QEMU options:
```bash
# Minimal config
qemu-system-x86_64 -enable-kvm -m 4096 -cdrom phazeos-build/out/archlinux-2025.12.08-x86_64.iso -boot d

# With virtual disk
qemu-system-x86_64 -enable-kvm -m 6144 -drive file=phazeos-test-disk.qcow2,format=qcow2 -cdrom phazeos-build/out/archlinux-2025.12.08-x86_64.iso -boot d
```

## Next Steps

1. **Wait longer** - Give it 15+ minutes
2. **Check boot menu** - Press keys when QEMU starts
3. **Try VirtualBox** - Might work better than QEMU
4. **Rebuild ISO** - If it's definitely broken
5. **Test on real hardware** - Write to USB and boot

## Quick Commands

```bash
# Kill QEMU
pkill -9 qemu-system-x86_64

# Check if running
ps aux | grep qemu

# Boot with virtual disk
qemu-system-x86_64 -enable-kvm -cpu host -m 6144 -smp 4 \
  -drive file=phazeos-test-disk.qcow2,format=qcow2 \
  -cdrom phazeos-build/out/archlinux-2025.12.08-x86_64.iso \
  -boot d -vga virtio -display gtk
```
