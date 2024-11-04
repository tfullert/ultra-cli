# UltraDNS CLI Tool

This is a command line interface for interacting with the UltraDNS platform.  It provides a set of commands, sub-commands, and options for listing (ls) zones and records, generating usage reports, and
creating/updating/deleting zone and record values.

Jump To:

* [Getting Started](#Getting-Started)
* [Usage](#Usage)
* [Functionality](#Functionality)
* [Contributing](#Contributing)
* [License](#License)
* [Questions](#Questions)

## Getting Started

### Dependencies and Installation

The dependencies for ultra-cli can be installed by running the following command in the folder where requirements.txt is:

```
pip install -r requirements.txt
```

You can also use PyInstaller to package ultra-cli into a standalone executable:

```bash
# Create single file executable
pip install pyinstaller
pyinstaller -F ultra-cli.py

# Executable will be in dist/ultra-cli
cp dist/ultra-cli.exe ultra-cli
```

## Usage

### Authentication

The UltraDNS CLI can use a username/password or an existing bearer token for authentication.  The username/password will be used if both username/password and token are specified.  You can specify values on the command line:

```bash
# Specify username/password on the command line
python ultra-cli.py --username=<USERNAME> --password=<PASSWORD> ls zones

# Or specify token on the command line
python ultra-cli.py --token=<TOKEN> ls zones
```

Or you can specify authentication parameters in the shell's environment variables:

```bash
# Specify username/password in the shell's environment
export ULTRA_UNAME=<USERNAME>
export ULTRA_PWORD=<PASSWORD>
python ultra-cli.py ls zones

# Or specify token in the shell's environment
export ULTRA_TOKEN=<TOKEN>
python ultra-cli.py ls zones
```

Token access will be limited to read-only functions in the CLI (listing and reporting).

### Quick Examples

Some examples of using the ultra-cli to list details about zones and records:

```bash
# List zones
python ultra-cli.py ls zones

# List zones by type
python ultra-cli.py ls zones --type=PRIMARY

# List zones and filter by name
python ultra-cli.py ls zones --name=prod

# List zones that are suspended
python ultra-cli.py ls zones --status=SUSPENDED

# List secondary zones that have 'api' in the name and export the list to a file
python ultra-cli.py ls zones --type=SECONDARY --name=api --export=sec_api_zones.csv

# List records for all zones in the account
python ultra-cli.py ls records

# List records for a subset of zones
python ultra-cli.py ls records --zone=example.com --zone=example.net

# List all 'www' records in all zones in the account and export the list to a file
python ultra-cli.py ls records --owner=www --export=all_www_records.csv
```

## Functionality

Only list (ls) functionality is available at this time.  Efforts will be made to continue development of the ultra-cli utility to include reporting, zone/record creation, update, and deletion.  Any contributions from the UltraDNS community would be greatly appreciated.

## Contributing

Contributions are always welcome! Please open a pull request with your changes, or open an issue if you encounter any problems or have suggestions.

## License
This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for more details.

## Questions

Please contact Tyler Fullerton (tyler.fullerton@vercara.com) if you have any questions or encounter any issues with this code.
