# theme/

The Windows XP "Luna"-style look for the XFCE desktop. **No Microsoft assets are
shipped** — this is open-licensed look-alike theming plus user-supplied art.

## Contents

| Path | What it is |
|------|------------|
| `install-theme.sh` | Installs the GTK theme + icons, sets the wallpaper, and seeds the XFCE config. Run by the provisioner. |
| `xfce4/xfconf/...`  | XFCE settings: XP-style GTK/WM theme selection and the bottom "taskbar" panel layout (Start menu, task list, tray, clock). |
| `wallpaper/`        | Drop a `bliss.png` here, or let the installer generate a Bliss-style placeholder. |

## How the XP look is assembled

1. **GTK theme** — an open XP-style theme (default: B00merang's "Windows XP")
   cloned into `/usr/share/themes`. Gives buttons, scrollbars, and window
   chrome the Luna look.
2. **Icons** — Papirus (from apt) as a clean stand-in; swap for an XP icon set
   if you have one licensed to redistribute.
3. **Panel** — a single locked bottom panel: Whisker "Start" menu + task list +
   system tray + a 12-hour clock, mirroring the XP taskbar.
4. **Wallpaper** — your `bliss.png`, or a generated green-hills gradient.

## Customizing

Edit the XML under `xfce4/xfconf/xfce-perchannel-xml/` to tweak the panel,
fonts, or theme names, then re-run `install-theme.sh`. To use a different GTK
theme entirely, change `XP_GTK_THEME_REPO` / `XP_GTK_THEME_NAME` at the top of
`install-theme.sh` and the `ThemeName` in `xsettings.xml`.
