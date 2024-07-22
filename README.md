# linuxmuster-cli7

CLI tools for the linuxmuster.net community.

Actually, followings commands are available (add `--help` to display all options):

 * `lmncli version` : Show versions of installed linuxmuster.net packages
 * `lmncli devices FILTER_STR` : List all devices which hostname, mac or room containing FILTER_STR. Gives all devices when FILTER_STR is emtpy.
 * `lmncli linbo groups` : Display all available linbo groups.                          
 * `lmncli linbo images` : Display all available linbo images.                      
 * `lmncli linbo lastsync GROUP` : Display last synchronisation date for all devices or the selected GROUP, or all if GROUP is empty
 * `lmncli samba dns` : Display all current DNS enries.
 * `lmncli samba drives` : Display all configured drives in linuxmuster.net for the specified school.
 * `lmncli samba gpos` : Display all GPOS details on the system.
 * `lmncli samba status` : Display all current samba connections.
 * `lmncli up GROUP` : Check if the clients are online. Specify GROUP to filter the results.
 * `lmncli user USER` : Show details of user USER.
 * `lmncli users FILTER_STR` : List all users which name, login or role containing FILTER_STR. Give all users if FILTER_STR is empty.

## Maintenance Details

Linuxmuster.net official | ❌ NO*
:---: | :---: 
[Community support](https://ask.linuxmuster.net) | ✅  YES**
Actively developed | ✅  YES
Primary maintainer | arnaud@linuxmuster.net
    
\* Even though this is not an official package, pull requests and issues are being looked at.  
** The linuxmuster community consits of people who are nice and happy to help. They are not directly involved in the development though, and might not be able to help in any case.

## Screenshots

![20240105-144325 resized](https://github.com/linuxmuster/linuxmuster-cli7/assets/10401079/d7fee874-155f-4faa-9628-24024fc9bc9b)

![20240105-144209 resized](https://github.com/linuxmuster/linuxmuster-cli7/assets/10401079/392ff5bd-2b51-4d1c-8eff-eab8257268e5)

![20240105-144107 resized](https://github.com/linuxmuster/linuxmuster-cli7/assets/10401079/7ebc2860-da55-4c54-b2dd-2ffb412c3c61)
