# Bone Chain Renamer

![Blender](https://img.shields.io/badge/Blender-4.2%2B-orange?logo=blender&logoColor=white)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Downloads](https://img.shields.io/github/downloads/aesu3d/Bone-Chain-Renamer/total)

A lightweight Blender addon that renames entire bone chains in a single click! ^-^
Made to quickly name long bone chains (like hair strands, skirts, ribbons, tails, or accessories) with numbers, prefixes, and left/right sides, without having to click and type every single bone name by hand!

<img width="800" height="805" alt="Animation-ezgif com-optimize" src="https://github.com/user-attachments/assets/9d942c40-f98f-4ce0-bb09-49fe09e35d45" />

## Features
- **One-Click Chain Rename:** Select the first bone and automatically rename everything parented below it in order! Also handles branching chains.
- **Smart Mirroring & Sides:** Detects `_L` and `_R` from the old name or 3D position, and can automatically rename the matching chain on the opposite side at the exact same time!
- **Custom Formatting & Prefix Tools:** Customize your starting number, number padding (`01`, `02`), and separators, plus quick buttons to stamp or peel prefixes on any selected bones.
- **Clean Workspace:** Located in the **AESU** sidebar tab (`N`) and only shows up when you have an Armature selected to keep your UI nice and tidy . ^-^

## Installation
1. Download the latest `.zip` from [Releases](https://github.com/aesu3d/Bone-Chain-Renamer/releases)
2. In Blender: **Edit → Preferences → Get Extensions → ⌄** (top right dropdown) **→ Install from Disk**.

*Tip: You can also just drag and drop the `.zip` file right into Blender's 3D Viewport to install it!!*

Requires Blender 4.2+, works up until the latest ver.

## How to use
1. Select your armature and switch to **Edit** or **Pose** mode (works in Object mode too!)
2. Press `N` to open the sidebar and click on the **AESU** tab.
3. Click the first bone of the chain you want to rename.
4. Type in your desired **Name** and tweak your settings, check the live **Example** preview at the bottom!)
5. Click **Rename Chain** to rename the whole chain (and mirrored chain if any) instantly!
6. Need to batch-edit prefixes? Just select any bones, type a **Prefix**, and click **Add Prefix** or **Remove Prefix**

## Support
Found a bug or have an idea? Open an [Issue](https://github.com/aesu3d/Bone-Chain-Renamer/issues)!! (´• ω •`)ﾉ

🛍️ More of my work: [aesu3d.com](https://aesu3d.com)

## License
GPL-3.0, see [LICENSE](LICENSE)
