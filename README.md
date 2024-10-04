# ConfigGuard
ConfigGuard simplifies the backup process for Cisco router and switch configurations, abstracting the complexities of interfacing with SolarWinds SWIS and CSV files. Its intuitive, intent-based interface allows users to easily interact with the class and select their desired actions.

Optionally, you can use the setup_basic_logging_to_file function to enable file-based logging for ConfigGuard, or you can implement a custom logging solution.

##### TODO:
Future releases will have:
- setup_logging_to_file
    - The ability to specify the logging file
- backup_all_devices
    - The ability to specify the backup folder
- Threading
    - Speedup the backup processes by introducing threads.

## Requirements:
### Python packages:
* pip3 install netmiko
* pip3 install orionsdk

### Environment_variables:
#### example: /etc/environment
* swis_username="admin"
* swis_password="Qwerty!1234"
* swis_server="solarwinds.example.com"
* network_username='UberAccount'
* network_password='Qwerty!0987'
* network_enable=None

### SolarWinds requirements:
#### Custom property
- ConfigGuard
    - To enable configuration backups for Cisco nodes within SolarWinds, ensure that each node has the custom property 'ConfigGuard' assigned.

### CSV requirements:
#### CSV file with credentials
headers
```
hostname, ipAddress, network_username, network_password, network_enable

```
#### CSV file without credentials
```
hostname,ipAddress
```

#### Example usage:
##### Populate from SolarWinds:
```
from ConfigGuard import network_nodes



nodes = network_nodes()

#Optional.
nodes.setup_basic_logging_to_file()

#Populate from SolarWinds.
nodes.populate_from_solarwinds()

#Backup all devices.
nodes.backup_all_devices()

```
##### Populate from csv with credentials:
```
from ConfigGuard import network_nodes



nodes = network_nodes()

#Optional.
nodes.setup_basic_logging_to_file()

#Populate from csv.
nodes.populate_from_csv('device_list_with_credentials.csv')

#Backup all devices.
nodes.backup_all_devices()
```
##### Populate from csv without credentials:
```
from ConfigGuard import network_nodes



nodes = network_nodes()

#Optional.
nodes.setup_basic_logging_to_file()

#Populate from csv using environment variable for credentials.
nodes.populate_from_csv('device_list_without_credentials.csv',True)

#Backup all devices.
nodes.backup_all_devices()
```