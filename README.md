# Cider Media Player Integration for Home Assistant

This custom component integrates the Cider Music Player with Home Assistant, allowing you to control and monitor your Cider player through the Home Assistant interface.

## Features

- Media playback control (play, pause, next, previous)
- Volume control
- Track information display
- Player status monitoring

## Installation

### Manual Installation

1. Copy the `cider_player` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the Home Assistant UI: **Settings** → **Devices & Services** → **+ ADD INTEGRATION** → Search for "Cider Media Player"

## Configuration

This integration supports config flow, which means you can configure it entirely through the Home Assistant UI. No manual YAML configuration is required.

### Required Information

- Cider player's IP address
- Port number (if different from default)
- Cider API Token (If enabled)

## Requirements

- Home Assistant Core
- Cider Music Player running on your network
- `aiohttp` Python package (automatically installed)

## Support

For bugs, feature requests, or support questions, please create an issue on the [GitHub repository](https://github.com/chrispycode/cider_player).

## License

This project is licensed under the MIT License

## Contributors

- [@chrispycode](https://github.com/chrispycode) - Maintainer

