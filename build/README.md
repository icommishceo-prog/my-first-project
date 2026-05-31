# build/ — live ISO builder

Builds a bootable BlissOSINT live ISO with Debian `live-build`. This is the
"real distro" path; for most learning use the simpler
[`provision/`](../provision) route instead.

## Requirements

- A **Debian** host (Debian 12 recommended; building on Ubuntu can work but
  Debian is the supported path).
- Packages: `sudo apt-get install live-build`
- Several GB of free disk and a decent internet connection (the build
  debootstraps a full Debian system and downloads all packages).
- Root (live-build mounts and chroots).

## Build

```bash
sudo ./build/build.sh
```

Output: `build/bliss-osint-bookworm-YYYYMMDD.iso`.

Override the Debian suite if you want:

```bash
sudo BLISS_DIST=trixie ./build/build.sh
```

## How it works

1. `lb config` scaffolds a live-build tree under `build/work/`.
2. The apt list is generated from [`provision/packages.apt`](../provision/packages.apt)
   (plus the `live-boot`/`live-config` runtime), so the ISO and the in-place
   provisioner install the same things.
3. The whole repo's `provision/`, `theme/`, and `docs/` are copied into the image.
4. A **chroot hook** runs inside the building image to install the pipx OSINT
   tools system-wide and apply the XP theme into `/etc/skel`.
5. `lb build` produces the hybrid ISO; the script renames it into `build/`.

## Try the ISO

Boot it in a VM (VirtualBox, QEMU/KVM, VMware). Snapshot before you start
investigating, treat the VM as disposable, and read
[`docs/opsec.md`](../docs/opsec.md).

## Notes

- `build/work/` is throwaway build state and is git-ignored.
- If a package is unavailable in your chosen suite, edit the package lists and
  rebuild.
