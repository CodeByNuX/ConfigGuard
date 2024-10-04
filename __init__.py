import os
import csv
import logging
import datetime
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from orionsdk import SwisClient

class _credentials:
    def __init__(self):
        self.network_username = None
        self.network_password = None
        self.network_enable = None

        
    
    def use_environment(self):
        """Populate credentials from environment variables."""
        try:
            self.network_username = os.environ['network_username']
            self.network_password = os.environ['network_password']
            self.network_enable = os.environ['network_enable']
            logging.info("Credentials populated from environment variables.")
        except KeyError as e:
            logging.error(f"Environment variable {str(e)} is missing.")
            raise


class _network_device:
    def __init__(self, hostname, ip_address, domain_name, creds):
        self.hostname = hostname
        self.ip_address = ip_address
        self.domain_name = domain_name
        self.creds = creds


class network_nodes:
    """ Main class to work with ConfigGuard."""
    def __init__(self):
        self.devices = []

    def setup_basic_logging_to_file(self):
        # Setting up logging.
        logging.basicConfig(
            filename='ConfigGuard.log', 
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s'
)


    
    def populate_from_solarwinds(self):
        """Populate network devices list from SolarWinds SWIS query."""

        try:
            #Solarwinds Nodes must have custom properties: ConfigGuard
            query = """SELECT Nodes.NodeID, Nodes.DisplayName, Nodes.IPAddress FROM Orion.Nodes INNER JOIN Orion.NodesCustomProperties ON Nodes.NodeID =NodesCustomProperties.NodeID WHERE NodesCustomProperties.ConfigGuard = TRUE"""

            try:
                swis_username = os.environ['swis_username']
                swis_password = os.environ['swis_password']
                swis_server = os.environ['swis_server']
                swis_client = SwisClient(swis_server,swis_username,swis_password)
            except KeyError as e:
                logging.error(f"Environment variable {str(e)} is missing.")
                raise


            response = swis_client.query(query)
            creds = _credentials()
            creds.use_environment()  # Use environment credentials
            
            for result in response['results']:
                hostname = result.get('DisplayName')  # Assuming DisplayName is the hostname
                ip_address = result.get('IPAddress')
                domain_name = 'unknown_domain'  # Can be retrieved later
                device = _network_device(hostname, ip_address, domain_name, creds)
                self.devices.append(device)
                
            logging.info(f"Devices populated from SolarWinds: {len(self.devices)} devices found.")
        
        except Exception as e:
            logging.error(f"Error querying SolarWinds: {e}")
            raise
    
    def populate_from_csv(self, csv_file, use_environment_variable_for_credentials:bool=False):
        """Populate network devices list from a CSV file."""
        try:
            with open(csv_file, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    hostname = row['hostname']
                    ip_address = row['ipAddress']
                    domain_name = 'unknown_domain'  # Can be retrieved later
                    creds = _credentials()
                    if use_environment_variable_for_credentials == False:
                        creds.network_username = row['network_username']
                        creds.network_password = row['network_password']
                        creds.network_enable = row['network_enable']
                    else:
                        creds.use_environment()
                    device = _network_device(hostname, ip_address, domain_name, creds)
                    self.devices.append(device)
                
            logging.info(f"Devices populated from CSV: {len(self.devices)} devices found.")
        
        except FileNotFoundError:
            logging.error(f"CSV file not found: {csv_file}")
            raise
        except KeyError as e:
            logging.error(f"Missing column in CSV: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Error reading CSV file {csv_file}: {e}")
            raise
    
    def _connect_and_backup(self, device:_network_device):
        """Connect to a network device and back up its configuration after checking if it's reachable."""        
        
        try:
            net_connect = ConnectHandler(
                device_type='cisco_ios',
                host=device.ip_address,
                username=device.creds.network_username,
                password=device.creds.network_password,
                secret=device.creds.network_enable
            )
            net_connect.enable()
            logging.info(f"Connected to {device.hostname} ({device.ip_address})")

            # Issue show commands
            config = net_connect.send_command("show running-config")
            
            # Detect for Invalid input '^'
            _domain_name = net_connect.send_command('show ip domain')
            if '^' in _domain_name:
                _domain_name = net_connect.send_command('show run | i ip domain name')
                _domain_name = _domain_name.replace('ip domain name','')

            device.domain_name = _domain_name.strip()

            # Save the configuration
            self._save_backup(device, config)
            
            net_connect.disconnect()
            logging.info(f"Backup completed for {device.hostname} ({device.ip_address})")

        except NetmikoTimeoutException as e:
            logging.error(f"Error timeout connecting to {device.hostname} ({device.ip_address})")
        except NetmikoAuthenticationException as e:
            logging.error(f"Error authenticating to {device.hostname} ({device.ip_address})")
        except Exception as e:
            logging.error(f"Error connecting to {device.hostname} ({device.ip_address}): {e}")
    
    def _save_backup(self, device:_network_device, config):
        """Save the backup configuration to a file."""
        try:
            
            backup_dir = os.path.join(os.getcwd(), device.domain_name)
            datetime_now = datetime.datetime.now()
            formatted_date_time = datetime_now.strftime("%y.%m.%d.%H.%M.%S")
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, f"{device.hostname}_{formatted_date_time}_backup.txt")
            
            with open(backup_file, 'w') as f:
                f.write(config)
            
            logging.info(f"Backup saved for {device.hostname} at {backup_file}")
        
        except IOError as e:
            logging.error(f"File I/O error while saving backup for {device.hostname}: {e}")
            raise
    
    def backup_all_devices(self):
        """Backup configuration for all devices."""
        for device in self.devices:
            logging.info(f"Starting backup for device {device.hostname} ({device.ip_address})")
            self._connect_and_backup(device)
