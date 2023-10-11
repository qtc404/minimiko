# Minimiko

Minimiko use Paramiko library to connect with devices via ssh and
recover info in json format. It's simplier than netmiko. This
library is work in progress.

## Example

```
>>> from minimiko import Device

>>> olt = Device('192.168.15.2', 'admin', 'admin')
>>> onts = olt.run('/dhcp/leases/show')

{'your_permission_group_is': 'administrator(15)', 0: {'slot': '1', 'port': 'PON 4', 'onu_id': '11', ... }}

```