# Deployer #

### Easy deploy to rancher tool ###
Suitable for Gitlab CI pipelines or manual deploy to rancher without GUI.
Adding extended ACL for user on stacks level. 

#### Required environmental variables ####
* RANCHER_URL
* RANCHER_ACCESS_KEY
* RANCHER_SECRET_KEY
* ACL_DB (example string - *postgres://deployer:@password@some.host/db_acl*)

#### Command ####

**Deploy service:**
*deployer StackName ServiceName ImageTag ImageName(optional)* 

**Rollback service:**
*deployer StackName ServiceName rollback* 

**Deploy stack:**
*deployer StackName all ImageTag ImageName(optional)* 

**Rollback stack:**
*deployer StackName all rollback* 

#### ACL DB structure ####

![picture alt](https://github.com/artemantipov/rancher-cli-deployer/blob/master/bd_structure.png "ACL DB Structure")
