# LDAPConnector

LdapConnector is a simple way to get data from the ldap tree in the linuxmsuter.net's project, used in the Webui to accelerate some response time.

## Examples

### Filter atributes in a response

Just import the LdapReader obejct to start send requests.
By default, a request will ship all attributes specified in the models, but you can filter it with the parameter list `attributes`:

```
>>> from linuxmusterTools.ldapconnector import LMNLdapReader as lr
>>> # Getting all schoolclasses
>>> lr.get('/schoolclasses', attributes=['cn'])
[{'cn': '8b'}, {'cn': '8d'}, {'cn': '12b'}, {'cn': '10b migrated'}, {'cn': '10atest'}, {'cn': '5a'}, ...]
>>> # Searching student with 'bla' in cn
>>> lr.get('/users/search/student/bla', attributes=['cn', 'homeDirectory'])
[{'cn': 'bla2', 'homeDirectory': '\\\\lmn\\default-school\\students\\15z\\bla2'}, {'cn': 'bla', 'homeDirectory': '\\\\lmn\\default-school\\students\\attic\\bla'}, {'cn': 'bla1', 'homeDirectory': '\\\\lmn\\default-school\\students\\15z\\bla1'}, {'cn': 'blatrule', 'homeDirectory': '\\\\lmn\\default-school\\students\\10a\\blatrule'}, {'cn': 'mablat', 'homeDirectory': '\\\\lmn\\default-school\\students\\blabla\\mablat'}]
```

### Sorting

When getting many objects, you can use the parameter `sortkey`:

```
>>> lr.get('/schoolclasses', attributes=['cn'], sortkey='cn')
[{'cn': '5a'}, {'cn': '8b'}, {'cn': '8d'}, {'cn': '10atest'}, {'cn': '10b migrated'}, {'cn': '12b'}, ...]
```

### Output type

If a response contains many items, you get a list of dict, but with the boolean parameter `dict`, you can switch to a dataclass object:

```
>>> lr.get('/schools', dict=False)
[LMNSchool(ou='default-school', distinguishedName='OU=default-school,OU=SCHOOLS,DC=linuxmuster,DC=lan')]
```

The object models are all defined in the models subdirectory.

## Available requests

At this point, the following requests are available:

  * `/projects` : get all projects
  * `/projects/PROJECT` : get all informations about a single project named `PROJECT`
  * `/roles/ROLE` : get all users in a specific `ROLE` ( `ROLE` can be e.g. `teacher`, `globaladministrator`, ... ) 
  * `/schoolclasses` : get all schoolclasses
  * `/schoolclasses/SCHOOLCLASS` : get all informations about a single schoolclass named `SCHOOLCLASS`
  * `/schoolclasses/SCHOOLCLASS/students` : get all students informations about a single schoolclass named `SCHOOLCLASS`
  * `/schoolclasses/search/QUERY` : if `QUERY` is e.g. 10, search all schoolclasses whose names contain 10
  * `/schools` : get a collection of all schools in a multischool environment, models.LMNSchool, subdn='OU=SCHOOLS,')
  * `/users` : get all users
  * `/users/USERNAME` : get all informations about the user `USERNAME` ( as `cn` )
  * `/users/search/SELECTION/QUERY` : get all users matching the `SELECTION` and `QUERY` criterias. `SELECTION` is role-based and can be set to `all`, `admins` or a specific role like `student`. `QUERY` is string which should be contained in the `cn`.