How to setup runbot 13.0.5.0.0 to run your project

Prerequisites:

* postgresql
*




Create a specific cluster


sudo su postgres
pg_createcluster -d /home/postgresql/clusters/10/runbot -p 5444 10 runbot 
pg_ctlcluster 10 runbot start
createuser -p 5444 -s runbot


then run ./install.sh
