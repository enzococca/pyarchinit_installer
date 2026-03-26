# PyArchInit Installer

A QGIS plugin to easily install and update PyArchInit directly from GitHub.

## Features

- Download and install PyArchInit from GitHub
- Choose between stable (master) or development (qt6-migration) branch
- Automatic detection of existing installations
- Proper handling of plugin folder naming
- Clean removal of old versions before installation

## Installation

1. Copy the `pyarchinit_installer` folder to your QGIS plugins directory:
   - **Windows**: `C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

2. Restart QGIS

3. Enable the plugin in **Plugins > Manage and Install Plugins > Installed**

## Usage

1. Open QGIS
2. Go to **Plugins > PyArchInit Installer > Install/Update PyArchInit**
3. Select the version you want to install:
   - **Master (Stable)**: Recommended for production use
   - **Development (Qt6 Migration)**: Latest features, may be unstable
4. Click **Install / Update**
5. Wait for the installation to complete
6. Restart QGIS to load the newly installed plugin

## Notes

- The plugin will automatically remove any existing PyArchInit installation
- The installed plugin will always be named `pyarchinit` regardless of the source branch
- An internet connection is required to download the plugin from GitHub

## Icon

If the icon doesn't display correctly, convert `icon.svg` to `icon.png`:

```bash
# Using ImageMagick
convert icon.svg icon.png

# Or using Inkscape
inkscape icon.svg --export-filename=icon.png --export-width=64 --export-height=64
```

## License

GPL v2
