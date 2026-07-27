<!-- <img src="./assets/coa_tools_logo.png" width="250"> -->

# COA tools 2

the Addon of Cutout Animation Tools for Blender, which allows you to create cutout animations in Blender.
<!--
[![GitHub release](https://img.shields.io/github/release/hcqmaker/coa_tools2.svg)](https://github.com/hcqmaker/coa_tools2/releases) 
-->

## Table of Contents

- [COA tools 2](#coa-tools-2)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Download and Installation](#download-and-installation)
    - [Download](#download)
    - [Installation](#installation)
      - [Photoshop Exporter](#photoshop-exporter)
      - [GIMP Exporter](#gimp-exporter)
      - [Blender Addon](#blender-addon)
      - [Krita PLugin](#krita-plugin)
  - [Development](#development)
    - [Documentation for development](#documentation-for-development)

## Description

COA Tools 2 is an add-on developed by [ndee89](https://github.com/ndee85) and modified/remade by [Aodaruma](https://github.com/Aodaruma/coa_tools2) [hcqmaker](https://github.com/hcqmaker/coa_tools2) which enables 2D rigging and animation within Blender.

[The original COA Tools by ndee89](https://github.com/ndee85/coa_tools) provided a rapid workflow for creating 2D cutout characters/animations in Blender. With COA Tools 2, the goal is to support Blender 3.4 and above, introduce automatic mesh generation, and establish a workflow with minimal features, allowing direct editing without going through proprietary modes.

The current Blender add-on release is tested with Blender 5.1.

Currently, the focus for development is on two aspects:

1. Photoshop sprite exporter
2. Blender add-on

The intention is to concentrate on these areas, specifically addressing the necessary improvements.

Since development is a time and resource-intensive process, it's not easy to being solely undertaken by me. However, if there are multiple developers willing to contribute and if the project necessitates scalability, I am considering inviting collaborators to join :)


#### Photoshop Exporter

![Photoshop Exporter](./assets/PS_exporter.png)

1. Copy `Photoshop/BlenderExporter.jsx` to the Photoshop scripts folder.
    - Windows: `C:\Program Files\Adobe\Adobe Photoshop CC 20XX\Presets\Scripts`
    - MacOS: `/Applications/Adobe Photoshop CC 20XX/Presets/Scripts`
2. Open Photoshop and psd file you want to export.
3. Run the script from `File -> Scripts -> BlenderExporter.jsx` to export sprites

#### GIMP Exporter

![GIMP Exporter](./assets/GIMP_exporter.png)

Referenced from [here](https://docs.gimp.org/en/install-script-fu.html)

1. Open GIMP and go to `Edit -> Preferences -> Folders -> Plugins` to find the plugin folder.
2. For GIMP 3.0.x, copy the `GIMP/coatools_exporter_gimp3` folder to the GIMP plugin folder. For GIMP 2.x, copy `GIMP/coatools_exporter.py` to the GIMP plugin folder.
3. Restart GIMP.
4. Open GIMP and xcf file you want to export.
5. Run the script from `File -> Export to CoaTools...` to export sprites

#### Blender Addon

The Blender add-on is tested with Blender 5.1.2

1. Open Blender and go to `Edit -> Preferences -> Add-ons -> Install...`
2. Select `coa_tools2.zip` and click `Install Add-on from File...` to install.
3. Enable `COA Tools 2` add-on.
4. Once the add-on is activated, go to `View -> Sidebar -> COA Tools 2` to open the COA Tools 2 panel.

#### Krita PLugin

![Krita Plugin](./assets/Krita_exporter.png)

Referenced from [here](https://docs.krita.org/en/user_manual/python_scripting/install_custom_python_plugin.html)

1. Copy all content from the `/Krita` directory into these directories:
    - Windows: `%APPDATA%\krita\pykrita`
    - Linux: `$HOME/.local/share/krita/pykrita`
    - MacOS: `$HOME/Library/Application Support/krita/pykrita`
2. Open Krita.
3. Go to `Settings` -> `Configure Krita`.
4. Access the `Python Plugin Manager`.
5. Enable the `COA Tools Exporter` plugin.
6. Once the plugin is activated, go to `Settings` -> `Dockers`.
7. Enable the `COA Tools Exporter` docker.

To use the plugin select all the layers that should be exported, select export path, export name and press
Export Selected Sprites button.

## Tutorials
#### How to use coa tols 2
Have a Look big Picture [Tutorials](https://github.com/hcqmaker/coa_tools2/tutorials/sample_tutorials.jpg)


## Godot 4.7 Importer
1. Need to `Export godot 4.7` from `Blender COA Tools 2 Plugin` 
1. Need `Godot/coa_small_importer/` put into `addon/coa_small_importer/` and active
2. You will found a `COA Small Import` Button in 2D Editor View
3. Select Import Path and Output Path Click Import.

### Documentation for development

The project includes several markdown documentation files in the `docs/` directory:

- **[docs/overview.md](https://github.com/hcqmaker/coa_tools2/blob/master/docs/overview.md)**: Provides a general introduction to developing COA Tools 2

- **[docs/specification.md](https://github.com/hcqmaker/coa_tools2/blob/master/docs/specification.md)**: Contains technical specifications and requirements for the Blender addon, including class structure, core features, and utility functions.

- **[docs/properties.md](https://github.com/hcqmaker/coa_tools2/blob/master/docs/properties.md)**: Comprehensive reference documentation for all COA Tools 2 properties in Blender addon, organized by category with detailed descriptions and type information.
